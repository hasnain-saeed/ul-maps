from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

from operators.load_gtfs_table_operator import LoadAllGTFSTablesOperator
from operators.gtfs_download_operator import GTFSDownloadOperator
from operators.gtfs_quality_check_operator import GTFSQualityCheckOperator
from helpers.sql_queries import SqlQueries

# Configuration
GTFS_URL = "https://opendata.samtrafiken.se/gtfs/ul/ul.zip"
DATA_DIR = "/opt/airflow/data"
DOWNLOAD_DIR = f"{DATA_DIR}/downloads"
EXTRACT_DIR = f"{DATA_DIR}/extracted"

with DAG(
    dag_id="gtfs_static_load",
    schedule=None,  # Manual trigger only
    start_date=datetime(2025, 7, 14),
    catchup=False,
    tags=["gtfs", "static", "etl"],
    description="Download, validate and load GTFS static data into PostgreSQL database"
) as dag:

    download_gtfs = GTFSDownloadOperator(
        task_id="download_gtfs_data",
        gtfs_url=GTFS_URL,
        download_dir=DOWNLOAD_DIR,
        extract_dir=EXTRACT_DIR,
        api_key_var="STATIC_API_KEY"
    )

    quality_check = GTFSQualityCheckOperator(
        task_id="quality_check_gtfs_data",
        extract_dir=EXTRACT_DIR,
        fail_on_missing_optional=False,
        min_record_counts={
            'agency.txt': 1,
            'routes.txt': 1,
            'stops.txt': 10,
            'trips.txt': 1,
            'stop_times.txt': 10
        }
    )

    create_all_tables = SQLExecuteQueryOperator(
        task_id="create_all_tables",
        conn_id="gtfs_postgres",
        sql=SqlQueries.create_all_tables
    )

    load_all_gtfs = LoadAllGTFSTablesOperator(
        task_id="load_all_gtfs_tables",
        extract_dir=f"{EXTRACT_DIR}/{{{{ ds }}}}",
        postgres_conn_id="gtfs_postgres",
        truncate_tables=True,
        skip_missing_files=True
    )

    create_indexes = SQLExecuteQueryOperator(
        task_id="create_indexes",
        conn_id="gtfs_postgres",
        sql=SqlQueries.create_indexes
    )

    download_gtfs >> quality_check >> create_all_tables >> load_all_gtfs >> create_indexes
