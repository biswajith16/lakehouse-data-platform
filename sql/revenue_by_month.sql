SELECT d.year, d.month, SUM(o.order_total) AS revenue
FROM fact_orders AS o
JOIN dim_date AS d ON o.date_key = d.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
