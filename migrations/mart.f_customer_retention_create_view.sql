drop view if exists mart.f_customer_retention;
create view mart.f_customer_retention as 
with cte as(
select date_part('week', date_time) as weekley, date_part('month', date_time) as monthly, payment_amount, quantity , status, customer_id ,
	case when count(id) over(partition by customer_id order by date_time,id) = 1 then 'new' else 'old' end type_client
from staging.user_order_log uol)

select cte.weekley, cte.monthly, count(case when cte.type_client = 'new' then 1 end) new_customers_count,
	count(case when cte.type_client = 'old' then 1 end) returning_customers_count,
	count(case when cte.status = 'refunded' then 1 end) refunded_customer_count,
	sum(case when cte.type_client = 'new' then cte.payment_amount end) new_customers_revenue,
	sum(case when cte.type_client = 'old' then cte.payment_amount end) returning_customers_revenue,
	sum(case when cte.status = 'refunded' then cte.quantity end) customers_refunded
from cte
group by cte.weekley, cte.monthly