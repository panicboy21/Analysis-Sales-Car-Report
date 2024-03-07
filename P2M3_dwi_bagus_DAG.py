'''
=================================================
Milestone 3

Nama  : Dwi Bagus Prasetyo
Batch : FTDS-RMT-027

Program ini dibuat untuk melakukan automatisasi mengambil data dari PostgresSQL, Cleaning data dan menyimpan kedalam csv dan load data csv yang sudah clean ke ElasticSearch. 
Adapun dataset yang dipakai adalah dataset mengenai penjualan mobil di Amerika selama tahun 2022 - 2023.
=================================================
'''

# Import Library
import pandas as pd
import psycopg2 as db
import re
from datetime import date
import datetime as dt
from datetime import timedelta
from elasticsearch import Elasticsearch

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator



def fetch_postgresql():
    # Get data from postgres
    conn_string="dbname='airflow' host='postgres' user='airflow' password='airflow'" #password masing2
    conn=db.connect(conn_string)
    df=pd.read_sql("select * from table_m3", conn)
    print(df.head())

def CleanData():
    # get data from postgres
    conn_string="dbname='airflow' host='postgres' user='airflow' password='airflow'" #password masing2
    conn=db.connect(conn_string)
    df=pd.read_sql("select * from table_m3", conn)

    # Preprocess Column Name
    preprocess_col = []
    for col in df.columns:
        # Case Folding
        col = col.lower()

        # Non-letter removal (such as emoticon, symbol (like μ, $, 兀), etc
        col = re.sub("[^A-Za-z\s']", " ", col)
        
        # Remove white space
        col = col.strip()

        # replace middle white space with underscore
        col = col.replace(" ", "_")

        preprocess_col.append(col)

    df.columns = preprocess_col

    # Change datetime format for date column
    df['date'] = pd.to_datetime(df['date'])

    # Handle Duplicate
    if df.duplicated().sum() > 0:
        df.drop_duplicates(keep='last')

    # Handle missing value
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if col in df.select_dtypes(include='object').columns:
                df[col].fillna(df[col].mode())
            elif col in df.select_dtypes(include='number').columns:
                df[col].fillna(df[col].mean())
            elif col in df.select_dtypes(include='datetime').columns:
                df[col].fillna(date.today())
    
    # Remove symbol Â from value column type object
    for col in df.columns:
        if col in df.select_dtypes(include='object').columns:
            df[col] = df[col].str.encode('ascii', 'ignore').str.decode('ascii')


    # Save clean data to csv
    df.to_csv('/opt/airflow/dags/P2M3_dwi_bagus_data_clean.csv', index=False)
    print("-------Data Saved------")

def post_elasticsearch():
    # Post to elasticseaarch
    es = Elasticsearch(hosts='elasticsearch')
    df=pd.read_csv('/opt/airflow/dags/P2M3_dwi_bagus_data_clean.csv')
    for i,r in df.iterrows():
        doc=r.to_json()
        res=es.index(index="cleandata", doc_type="doc", body=doc)
        print(res)

default_args = {
    'owner': 'bagus',
    'start_date': dt.datetime(2024, 2, 23, 6, 29, 0) - dt.timedelta(hours=7),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=2),
}

with DAG('M3_PipeLine',
         default_args=default_args,
         schedule_interval='30 6 * * *',
         catchup = False
         ) as dag:

    fetchData = PythonOperator(task_id='fetchtopostgre',
                                 python_callable=fetch_postgresql)
    
    cleanData = PythonOperator(task_id='clean',
                                 python_callable=CleanData)

    postElastic = PythonOperator(task_id='postElastic',
                                 python_callable=post_elasticsearch)



fetchData >> cleanData >> postElastic