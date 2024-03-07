'''
=================================================
Milestone 3

Nama  : Dwi Bagus Prasetyo
Batch : FTDS-RMT-027

Program ini dibuat untuk melakukan automatisasi menyimpan data dari csv ke PostgreSQL. 
Adapun dataset yang dipakai adalah dataset mengenai penjualan mobil di Amerika selama tahun 2022 - 2023.
=================================================
'''

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
# from airflow.utils.task_group import TaskGroup
from datetime import datetime, date, timedelta
import datetime as dt
from sqlalchemy import create_engine #koneksi ke postgres
import pandas as pd

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


def load_csv_to_postgres():
    database = "airflow"
    username = "airflow"
    password = "airflow"
    host = "postgres"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engine = create_engine(postgres_url)
    # engine= create_engine("postgresql+psycopg2://airflow:airflow@postgres/airflow")
    conn = engine.connect()

    df = pd.read_csv('/opt/airflow/dags/P2M3_dwi_bagus_data_raw.csv')
    #df.to_sql(nama_table, conn, index=False, if_exists='replace')
    df.to_sql('table_m3', conn, index=False, if_exists='replace')

default_args = {
    'owner': 'bagus',
    'start_date': dt.datetime(2024, 2, 23, 6, 30, 0) - dt.timedelta(hours=7),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=2),
}

with DAG('insert_csv_to_postgres',
         default_args=default_args,
         schedule_interval='30 6 * * *',
         catchup = False
         ) as dag:

    csvtoPostgres = PythonOperator(task_id='csv_to_postgres',
                                 python_callable=load_csv_to_postgres)
    


csvtoPostgres