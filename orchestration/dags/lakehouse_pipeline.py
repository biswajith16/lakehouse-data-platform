"""Airflow orchestration that delegates work to the existing CLI engine."""

from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
from airflow import DAG

with DAG("lakehouse_demo_pipeline", start_date=datetime(2025, 1, 1), schedule=None, catchup=False, default_args={"retries": 2, "retry_delay": timedelta(minutes=2)}) as dag:
    generate = BashOperator(task_id="generate_demo_data", bash_command="python -m src.generators.generate_demo_data")
    bronze = BashOperator(task_id="bronze", bash_command="python run_pipeline.py --mode demo --stage bronze")
    silver = BashOperator(task_id="silver", bash_command="python run_pipeline.py --mode demo --stage silver")
    gold = BashOperator(task_id="gold", bash_command="python run_pipeline.py --mode demo --stage gold")
    generate >> bronze >> silver >> gold
