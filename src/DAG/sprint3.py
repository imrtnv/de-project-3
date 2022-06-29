import time
import requests
import json
import pandas as pd

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.hooks.base import BaseHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.http_hook import HttpHook


http_conn_id = HttpHook.get_connection('s3_conn')
api_key = http_conn_id.extra_dejson.get('aws_access_key_id')
base_url = http_conn_id.host


'''
s3_conn:
    host=https://d5dg1j9kt695d30blp03.apigw.yandexcloud.net
    extra={"aws_access_key_id": "5f55e6c0-e9e5-4a9c-b313-63c01fc31460"}

postgres_de:
    conn_type="Postgres",
    host="localhost",
    login="jovyan",
    password="jovyan",
    port="5432

postgres_conn_id = BaseHook.get_connection('postgres_de')
'''



postgres_conn_id = 'postgres_de'

nickname = "imartnv"
cohort = "2"

headers = {
    'X-Nickname': nickname,
    'X-Cohort': cohort,
    'X-Project': 'True',
    'X-API-KEY': api_key,
    'Content-Type': 'application/x-www-form-urlencoded'
}


def generate_report(ti):
    print('Making request generate_report')

    response = requests.post(f'{base_url}/generate_report', headers=headers)
    response.raise_for_status()
    task_id = json.loads(response.content)['task_id']
    ti.xcom_push(key='task_id', value=task_id)
    print(f'Response is {response.content}')


def get_report(ti):
    print('Making request get_report')
    task_id = ti.xcom_pull(key='task_id')

    report_id = None

    for i in range(7):
        response = requests.get(f'{base_url}/get_report?task_id={task_id}', headers=headers)
        response.raise_for_status()
        print(f'Response is {response.content}')
        status = json.loads(response.content)['status']
        if status == 'SUCCESS':
            report_id = json.loads(response.content)['data']['report_id']
            break
        else:
            time.sleep(10)

    if not report_id:
        raise TimeoutError()

    ti.xcom_push(key='report_id', value=report_id)
    print(f'Report_id={report_id}')


def get_increment(date, ti):
    print('Making request get_increment')
    report_id = ti.xcom_pull(key='report_id')
    response = requests.get(
        f'{base_url}/get_increment?report_id={report_id}&date={str(date)}T00:00:00',
        headers=headers)
    response.raise_for_status()
    print(f'Response is {response.content}')

    increment_id = json.loads(response.content)['data']['increment_id']
    ti.xcom_push(key='increment_id', value=increment_id)
    print(f'increment_id={increment_id}')


def upload_data_to_staging(filename, date, pg_table, pg_schema, ti):
    increment_id = ti.xcom_pull(key='increment_id')
    s3_filename = f'https://storage.yandexcloud.net/s3-sprint3/cohort_{cohort}/{nickname}/project/{increment_id}/{filename}'

    local_filename = date.replace('-', '') + '_' + filename

    response = requests.get(s3_filename)
    open(f"{local_filename}", "wb").write(response.content)

    df = pd.read_csv(local_filename)
    df.drop_duplicates(subset=['id'])
    df = df.drop(['id'], axis=1)
    df = df.drop_duplicates().reset_index(drop=True)

    postgres_hook = PostgresHook(postgres_conn_id)
    engine = postgres_hook.get_sqlalchemy_engine()
    df.to_sql(pg_table, engine, schema=pg_schema, if_exists='append', index=False)


args = {
    "owner": "student",
    'email': ['student@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0
}

business_dt = '{{ ds }}'

with DAG(
        'customer_retention',
        default_args=args,
        description='Provide default dag for sprint3',
        catchup=True,
        start_date=datetime.today() - timedelta(days=8),
        end_date=datetime.today() - timedelta(days=1),
) as dag:
    generate_report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report)

    get_report = PythonOperator(
        task_id='get_report',
        python_callable=get_report)

    get_increment = PythonOperator(
        task_id='get_increment',
        python_callable=get_increment,
        op_kwargs={'date': business_dt})

    add_column_user_order_log = PostgresOperator(
        task_id = 'add_column_user_order_log',
        postgres_conn_id = postgres_conn_id,
        sql="sql/staging.user_order_log_add_column.sql"
    )


    upload_user_order_inc = PythonOperator(
        task_id='upload_user_order_inc',
        python_callable=upload_data_to_staging,
        op_kwargs={'date': business_dt,
                   'filename': 'user_orders_log_inc.csv',
                   'pg_table': 'user_order_log',
                   'pg_schema': 'staging'})

    update_d_item_table = PostgresOperator(
        task_id='update_d_item',
        postgres_conn_id=postgres_conn_id,
        sql="sql/mart.d_item.sql")

    update_d_customer_table = PostgresOperator(
        task_id='update_d_customer',
        postgres_conn_id=postgres_conn_id,
        sql="sql/mart.d_customer.sql")

    update_d_city_table = PostgresOperator(
        task_id='update_d_city',
        postgres_conn_id=postgres_conn_id,
        sql="sql/mart.d_city.sql")

    update_f_sales = PostgresOperator(
        task_id='update_f_sales',
        postgres_conn_id=postgres_conn_id,
        sql="sql/mart.f_sales.sql",
        parameters={"date": {business_dt}}
    )

    customer_retention_view = PostgresOperator(
        task_id = 'customer_retention_view',
        postgres_conn_id=postgres_conn_id,
        sql = "sql/mart.f_customer_retention_create_view.sql"
    )


    (
            generate_report
            >> get_report
            >> get_increment
            >> add_column_user_order_log
            >> upload_user_order_inc
            >> [update_d_item_table, update_d_city_table, update_d_customer_table]
            >> update_f_sales
            >> customer_retention_view
    )