DO $$ BEGIN
	IF (select max(date_time) :: date from staging.user_order_log) = (select (now() - INTERVAL '1 DAY') :: date)
	THEN
	truncate table staging.user_order_log RESTART IDENTITY;
	truncate table mart.f_sales RESTART IDENTITY;
	END IF;
END$$; 