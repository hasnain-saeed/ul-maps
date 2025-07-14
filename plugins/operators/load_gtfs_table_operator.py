import os
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import BaseOperator
from airflow.exceptions import AirflowException


class LoadGTFSTableOperator(BaseOperator):
    """
    Loads GTFS CSV files into PostgreSQL tables using COPY command
    """

    ui_color = '#F98866'
    template_fields = ['file_path', 'data_dir']

    def __init__(self,
                 table_name,
                 file_path=None,
                 data_dir=None,
                 file_name=None,
                 postgres_conn_id="postgres_default",
                 truncate_table=False,
                 *args, **kwargs):

        super(LoadGTFSTableOperator, self).__init__(*args, **kwargs)
        self.table_name = table_name
        self.postgres_conn_id = postgres_conn_id
        self.truncate_table = truncate_table

        # Support both file_path and data_dir+file_name patterns
        if file_path:
            self.file_path = file_path
        elif data_dir and file_name:
            self.file_path = os.path.join(data_dir, file_name)
        else:
            raise ValueError("Either file_path or (data_dir + file_name) must be provided")

    def execute(self, context):
        self.log.info(f"Loading data into table: {self.table_name}")
        self.log.info(f"From file: {self.file_path}")

        # Check if file exists
        if not os.path.exists(self.file_path):
            raise AirflowException(f"File not found: {self.file_path}")

        # Get file size for logging
        file_size = os.path.getsize(self.file_path)
        self.log.info(f"File size: {file_size} bytes")

        # Get PostgreSQL connection
        postgres = PostgresHook(postgres_conn_id=self.postgres_conn_id)

        try:
            # Optionally truncate table before loading
            if self.truncate_table:
                truncate_sql = f"TRUNCATE TABLE {self.table_name};"
                postgres.run(truncate_sql)
                self.log.info(f"Truncated table: {self.table_name}")

            # Load data using COPY command
            copy_sql = f"""
            COPY {self.table_name} FROM '{self.file_path}'
            WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');
            """

            self.log.info(f"Executing COPY command: {copy_sql}")
            postgres.run(copy_sql)

            # Get record count after loading
            count_sql = f"SELECT COUNT(*) FROM {self.table_name};"
            result = postgres.get_first(count_sql)
            record_count = result[0] if result else 0

            self.log.info(f"Successfully loaded {record_count} records into {self.table_name}")

            return {
                'table_name': self.table_name,
                'file_path': self.file_path,
                'records_loaded': record_count,
                'file_size': file_size
            }

        except Exception as e:
            self.log.error(f"Failed to load data into {self.table_name}: {str(e)}")
            raise AirflowException(f"Data load failed: {str(e)}")


class LoadAllGTFSTablesOperator(BaseOperator):
    """
    Loads all GTFS tables from a directory in the correct order
    """

    ui_color = '#87CEEB'
    template_fields = ['extract_dir']

    # Loading order respecting foreign key dependencies
    TABLE_LOAD_ORDER = [
        # Independent tables first
        {'table': 'agency', 'file': 'agency.txt'},
        {'table': 'calendar', 'file': 'calendar.txt'},
        {'table': 'calendar_dates', 'file': 'calendar_dates.txt'},
        {'table': 'stops', 'file': 'stops.txt'},
        {'table': 'shapes', 'file': 'shapes.txt'},
        {'table': 'feed_info', 'file': 'feed_info.txt'},
        {'table': 'attributions', 'file': 'attributions.txt'},
        {'table': 'booking_rules', 'file': 'booking_rules.txt'},

        # Dependent tables
        {'table': 'routes', 'file': 'routes.txt'},
        {'table': 'trips', 'file': 'trips.txt'},
        {'table': 'stop_times', 'file': 'stop_times.txt'},
    ]

    def __init__(self,
                 extract_dir,
                 postgres_conn_id="postgres_default",
                 truncate_tables=False,
                 skip_missing_files=True,
                 *args, **kwargs):

        super(LoadAllGTFSTablesOperator, self).__init__(*args, **kwargs)
        self.extract_dir = extract_dir
        self.postgres_conn_id = postgres_conn_id
        self.truncate_tables = truncate_tables
        self.skip_missing_files = skip_missing_files

    def execute(self, context):
        self.log.info(f"Loading GTFS data from directory: {self.extract_dir}")

        if not os.path.exists(self.extract_dir):
            raise AirflowException(f"Extract directory not found: {self.extract_dir}")

        # Debug: List all files in extract directory
        try:
            all_files = os.listdir(self.extract_dir)
            self.log.info(f"Files found in {self.extract_dir}: {all_files}")
        except Exception as e:
            self.log.error(f"Could not list files in {self.extract_dir}: {str(e)}")

        results = []
        postgres = PostgresHook(postgres_conn_id=self.postgres_conn_id)

        for table_info in self.TABLE_LOAD_ORDER:
            table_name = table_info['table']
            file_name = table_info['file']
            file_path = os.path.join(self.extract_dir, file_name)

            self.log.info(f"Processing {table_name} from {file_name}")

            # Check if file exists (from Airflow perspective)
            if not os.path.exists(file_path):
                if self.skip_missing_files:
                    self.log.warning(f"File not found, skipping: {file_path}")
                    continue
                else:
                    raise AirflowException(f"Required file not found: {file_path}")

            # Check file size for debugging
            file_size = os.path.getsize(file_path)
            self.log.info(f"File {file_path} size: {file_size} bytes")

            try:
                # Truncate table if requested
                if self.truncate_tables:
                    truncate_sql = f"TRUNCATE TABLE {table_name} CASCADE;"
                    postgres.run(truncate_sql)
                    self.log.info(f"Truncated table: {table_name}")

                # Load data - PostgreSQL needs the EXACT same path
                # Both containers should see the same mounted volume
                copy_sql = f"""
                COPY {table_name} FROM '{file_path}'
                WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '');
                """

                self.log.info(f"Executing COPY command for {table_name}")
                self.log.info(f"PostgreSQL will look for file at: {file_path}")
                postgres.run(copy_sql)

                # Get record count
                count_sql = f"SELECT COUNT(*) FROM {table_name};"
                result = postgres.get_first(count_sql)
                record_count = result[0] if result else 0

                self.log.info(f"Loaded {record_count} records into {table_name}")

                results.append({
                    'table_name': table_name,
                    'file_name': file_name,
                    'records_loaded': record_count,
                    'status': 'success'
                })

            except Exception as e:
                error_msg = f"Failed to load {table_name}: {str(e)}"
                self.log.error(error_msg)
                results.append({
                    'table_name': table_name,
                    'file_name': file_name,
                    'records_loaded': 0,
                    'status': 'failed',
                    'error': str(e)
                })
                raise AirflowException(error_msg)

        # Summary
        total_records = sum(r['records_loaded'] for r in results)
        self.log.info(f"Loading complete. Total records loaded: {total_records}")

        return {
            'total_records': total_records,
            'tables_loaded': len(results),
            'results': results
        }
