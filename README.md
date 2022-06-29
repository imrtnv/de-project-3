# Проект 3

### Описание
Задача доработать пайплайн с учетом новых вводных
1) Учесть при обновлении добавление нового поля status и возвратных товаров
2) Разработать новую витрину mart.f_customer_retention 
 - weekley - номер недели
 - monthly - 
 - new_customers_count - Кол-во новых пользователей
 - returning_customers_count - Кол-во повторных пользователей
 - refunded_customer_count
 - new_customers_revenue
 - returning_customers_revenue
 - customers_refunded

### Как работать с репозиторием
1. В вашем GitHub-аккаунте автоматически создастся репозиторий 
`de-project-{{ номер проекта }}` после того, как вы привяжете свой 
GitHub-аккаунт на Платформе.
2. Скопируйте репозиторий на свой локальный компьютер:
    * `git clone https://github.com/{{ username }}/de-project-3.git`
    * `cd de-project-3`
3. Выполните проект и сохраните получившийся код в локальном репозитории:
	  * `git add .`
	  * `git commit -m 'my best commit'`
4. Обновите репозиторий в вашем GutHub-аккаунте:
	  * `git push origin main`

### Структура репозитория
1. Папка migrations хранит файлы миграции. 
Файлы миграции должны быть с расширением `.sql` и содержать SQL-скрипт обновления базы данных.
2. В папке src хранятся все необходимые исходники: 
    * Папка DAG содержит DAGs Airflow.

### Как запустить контейнер
Запустите локально команду:

`docker run -d --rm -p 3000:3000 -p 15432:5432 --name=de-project-sprint-3-server sindb/project-sprint-3:latest`

После того как запустится контейнер, у вас будут доступны:
1. Visual Studio Code
2. Airflow
3. Database
