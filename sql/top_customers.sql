SELECT c.customer_id, c.first_name, c.last_name, SUM(o.order_total) AS lifetime_revenue
FROM fact_orders AS o
JOIN dim_customer AS c ON o.customer_key = c.customer_key
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY lifetime_revenue DESC
LIMIT 10;
