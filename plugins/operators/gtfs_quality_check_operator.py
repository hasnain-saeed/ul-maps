import os
import pandas as pd
from airflow.models import BaseOperator
from airflow.exceptions import AirflowException


class GTFSQualityCheckOperator(BaseOperator):
    """
    Performs data quality checks on extracted GTFS files
    """

    ui_color = '#FFD700'

    # Required GTFS files and their expected columns
    REQUIRED_FILES = {
        'agency.txt': ['agency_id', 'agency_name', 'agency_url', 'agency_timezone'],
        'routes.txt': ['route_id', 'agency_id', 'route_type'],
        'stops.txt': ['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
        'trips.txt': ['route_id', 'service_id', 'trip_id'],
        'stop_times.txt': ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'],
        'calendar.txt': ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date']
    }

    # Optional files
    OPTIONAL_FILES = {
        'calendar_dates.txt': ['service_id', 'date', 'exception_type'],
        'shapes.txt': ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'],
        'feed_info.txt': ['feed_publisher_name', 'feed_publisher_url', 'feed_lang'],
        'attributions.txt': ['organization_name'],
        'booking_rules.txt': ['booking_rule_id', 'booking_type']
    }

    def __init__(self,
                 extract_dir="/opt/airflow/data/extracted",
                 fail_on_missing_optional=False,
                 min_record_counts=None,
                 *args, **kwargs):

        super(GTFSQualityCheckOperator, self).__init__(*args, **kwargs)
        self.extract_dir = extract_dir
        self.fail_on_missing_optional = fail_on_missing_optional
        self.min_record_counts = min_record_counts or {}

    def execute(self, context):
        # Get the timestamp from the download task
        timestamp = context['ds']
        data_path = os.path.join(self.extract_dir, timestamp)

        if not os.path.exists(data_path):
            raise AirflowException(f"Extract directory not found: {data_path}")

        self.log.info(f"Performing quality checks on GTFS data in: {data_path}")

        # Get list of files in the directory
        available_files = set(os.listdir(data_path))
        self.log.info(f"Available files: {sorted(available_files)}")

        quality_report = {
            'timestamp': timestamp,
            'data_path': data_path,
            'files_checked': {},
            'errors': [],
            'warnings': [],
            'summary': {}
        }

        # Check required files
        self._check_required_files(data_path, available_files, quality_report)

        # Check optional files
        self._check_optional_files(data_path, available_files, quality_report)

        # Check file contents and structure
        self._check_file_contents(data_path, available_files, quality_report)

        # Generate summary
        self._generate_summary(quality_report)

        # Log results
        self._log_results(quality_report)

        # Fail if there are critical errors
        if quality_report['errors']:
            raise AirflowException(f"Quality check failed with {len(quality_report['errors'])} errors")

        return quality_report

    def _check_required_files(self, data_path, available_files, quality_report):
        """Check if all required files are present"""
        for filename, required_columns in self.REQUIRED_FILES.items():
            if filename not in available_files:
                quality_report['errors'].append(f"Missing required file: {filename}")
            else:
                quality_report['files_checked'][filename] = {
                    'type': 'required',
                    'present': True,
                    'required_columns': required_columns
                }

    def _check_optional_files(self, data_path, available_files, quality_report):
        """Check optional files"""
        for filename, expected_columns in self.OPTIONAL_FILES.items():
            if filename in available_files:
                quality_report['files_checked'][filename] = {
                    'type': 'optional',
                    'present': True,
                    'expected_columns': expected_columns
                }
            else:
                quality_report['warnings'].append(f"Optional file not found: {filename}")
                if self.fail_on_missing_optional:
                    quality_report['errors'].append(f"Missing optional file: {filename}")

    def _check_file_contents(self, data_path, available_files, quality_report):
        """Check file contents and structure"""
        for filename, file_info in quality_report['files_checked'].items():
            if not file_info['present']:
                continue

            file_path = os.path.join(data_path, filename)

            try:
                # Read CSV file
                df = pd.read_csv(file_path)

                # Check if file is empty
                if df.empty:
                    quality_report['errors'].append(f"File {filename} is empty")
                    continue

                # Check columns
                actual_columns = set(df.columns)
                if 'required_columns' in file_info:
                    required_columns = set(file_info['required_columns'])
                    missing_columns = required_columns - actual_columns
                    if missing_columns:
                        quality_report['errors'].append(
                            f"File {filename} missing required columns: {missing_columns}"
                        )

                # Check record counts
                record_count = len(df)
                min_count = self.min_record_counts.get(filename, 0)
                if record_count < min_count:
                    quality_report['errors'].append(
                        f"File {filename} has {record_count} records, minimum required: {min_count}"
                    )

                # Update file info
                file_info.update({
                    'record_count': record_count,
                    'columns': list(actual_columns),
                    'file_size_mb': round(os.path.getsize(file_path) / 1024 / 1024, 2)
                })

                # Basic data validation
                self._validate_data_content(df, filename, quality_report)

            except Exception as e:
                quality_report['errors'].append(f"Error reading {filename}: {str(e)}")

    def _validate_data_content(self, df, filename, quality_report):
        """Perform basic data validation"""
        if filename == 'agency.txt':
            # Check for duplicate agency IDs
            if df['agency_id'].duplicated().any():
                quality_report['errors'].append(f"Duplicate agency_id found in {filename}")

        elif filename == 'stops.txt':
            # Check for valid coordinates
            if df['stop_lat'].isna().any() or df['stop_lon'].isna().any():
                quality_report['warnings'].append(f"Missing coordinates in {filename}")

            # Check coordinate ranges
            invalid_lat = (df['stop_lat'] < -90) | (df['stop_lat'] > 90)
            invalid_lon = (df['stop_lon'] < -180) | (df['stop_lon'] > 180)

            if invalid_lat.any() or invalid_lon.any():
                quality_report['errors'].append(f"Invalid coordinates in {filename}")

        elif filename == 'routes.txt':
            # Check for valid route types
            valid_route_types = {0, 1, 2, 3, 4, 5, 6, 7, 11, 12}
            invalid_types = set(df['route_type']) - valid_route_types
            if invalid_types:
                quality_report['warnings'].append(
                    f"Non-standard route types in {filename}: {invalid_types}"
                )

    def _generate_summary(self, quality_report):
        """Generate quality check summary"""
        total_files = len(quality_report['files_checked'])
        required_files = sum(1 for f in quality_report['files_checked'].values() if f['type'] == 'required')
        optional_files = sum(1 for f in quality_report['files_checked'].values() if f['type'] == 'optional')

        total_records = sum(f.get('record_count', 0) for f in quality_report['files_checked'].values())

        quality_report['summary'] = {
            'total_files': total_files,
            'required_files': required_files,
            'optional_files': optional_files,
            'total_records': total_records,
            'errors': len(quality_report['errors']),
            'warnings': len(quality_report['warnings']),
            'status': 'PASSED' if not quality_report['errors'] else 'FAILED'
        }

    def _log_results(self, quality_report):
        """Log quality check results"""
        summary = quality_report['summary']

        self.log.info("="*60)
        self.log.info("GTFS DATA QUALITY CHECK RESULTS")
        self.log.info("="*60)
        self.log.info(f"Status: {summary['status']}")
        self.log.info(f"Total Files: {summary['total_files']}")
        self.log.info(f"Required Files: {summary['required_files']}")
        self.log.info(f"Optional Files: {summary['optional_files']}")
        self.log.info(f"Total Records: {summary['total_records']}")
        self.log.info(f"Errors: {summary['errors']}")
        self.log.info(f"Warnings: {summary['warnings']}")

        if quality_report['errors']:
            self.log.error("ERRORS:")
            for error in quality_report['errors']:
                self.log.error(f"  - {error}")

        if quality_report['warnings']:
            self.log.warning("WARNINGS:")
            for warning in quality_report['warnings']:
                self.log.warning(f"  - {warning}")

        self.log.info("="*60)
