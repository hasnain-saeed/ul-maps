import os
import requests
import zipfile
from datetime import datetime
from airflow.models import BaseOperator
from airflow.models import Variable


class GTFSDownloadOperator(BaseOperator):
    """
    Downloads GTFS ZIP file from URL and extracts it to specified directory
    """

    ui_color = '#87CEEB'

    def __init__(self,
                 gtfs_url,
                 download_dir="/opt/airflow/data/downloads",
                 extract_dir="/opt/airflow/data/extracted",
                 api_key_var="GTFS_API_KEY",
                 *args, **kwargs):

        super(GTFSDownloadOperator, self).__init__(*args, **kwargs)
        self.gtfs_url = gtfs_url
        self.download_dir = download_dir
        self.extract_dir = extract_dir
        self.api_key_var = api_key_var

    def execute(self, context):
        # Get API key from Airflow Variables
        api_key = Variable.get(self.api_key_var, default_var=None)

        # Create directories if they don't exist
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.extract_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = context['ds']  # YYYY-MM-DD format
        zip_filename = f"gtfs_{timestamp}.zip"
        zip_path = os.path.join(self.download_dir, zip_filename)

        self.log.info(f"Downloading GTFS data from: {self.gtfs_url}")

        # Download the ZIP file
        try:
            params = {"key": api_key} if api_key else {}
            response = requests.get(self.gtfs_url, params=params, stream=True, timeout=60)
            response.raise_for_status()

            # Save the ZIP file
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.log.info(f"Downloaded ZIP file to: {zip_path}")

        except requests.exceptions.RequestException as e:
            self.log.error(f"Failed to download GTFS data: {str(e)}")
            raise

        # Extract the ZIP file
        extract_path = os.path.join(self.extract_dir, timestamp)

        # Clean existing directory to avoid stale files
        if os.path.exists(extract_path):
            import shutil
            shutil.rmtree(extract_path)
            self.log.info(f"Cleaned existing directory: {extract_path}")

        os.makedirs(extract_path, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            self.log.info(f"Extracted GTFS files to: {extract_path}")

            # List extracted files
            extracted_files = os.listdir(extract_path)
            self.log.info(f"Extracted files: {extracted_files}")

            # Clean up ZIP file
            os.remove(zip_path)
            self.log.info(f"Cleaned up ZIP file: {zip_path}")

        except zipfile.BadZipFile as e:
            self.log.error(f"Invalid ZIP file: {str(e)}")
            raise
        except Exception as e:
            self.log.error(f"Failed to extract ZIP file: {str(e)}")
            raise

        # Return the extract path for downstream tasks
        return {
            'extract_path': extract_path,
            'extracted_files': extracted_files,
            'timestamp': timestamp
        }
