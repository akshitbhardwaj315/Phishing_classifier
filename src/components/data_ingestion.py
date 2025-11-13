# src/components/data_ingestion.py

import sys
import os
import pandas as pd
from pathlib import Path
from src.constant import *
from src.exception import CustomException
from src.logger import logging
from dataclasses import dataclass

DEFAULT_DATA_PATH = os.path.join(os.getcwd(), "data", "phising.csv")

@dataclass
class DataIngestionConfig:
    raw_data_dir: str = os.path.join(artifact_folder, "data_ingestion")
    raw_data_filepath: str = os.path.join(raw_data_dir, "data.csv")

class DataIngestion:
    def __init__(self):
        self.data_ingestion_config = DataIngestionConfig()
        logging.info("Data Ingestion component initialized.")

    def get_data_from_source(self) -> pd.DataFrame:
        try:
            data_path = os.environ.get("DATA_PATH", DEFAULT_DATA_PATH)
            logging.info(f"Attempting to read data from: {data_path}")

            if not os.path.exists(data_path):
                logging.error(f"Data file not found at {data_path}")
                logging.info(f"--- IMPORTANT ---")
                logging.info(f"Please create a 'data' folder in your project's root directory.")
                logging.info(f"Then, move your 'phising.csv' file into that 'data' folder.")
                logging.info(f"Or, set a 'DATA_PATH' environment variable to the file's location.")
                logging.info(f"-----------------")
                raise FileNotFoundError(f"Data file not found: {data_path}")
            
            df = pd.read_csv(data_path)
            logging.info(f"Successfully loaded data from {data_path}, shape: {df.shape}")
            return df

        except Exception as e:
            raise CustomException(e, sys)

    def initiate_data_ingestion(self) -> str:
        logging.info("Entered initiate_data_ingestion method.")

        try:
            df = self.get_data_from_source()

            output_dir = self.data_ingestion_config.raw_data_dir
            output_filepath = self.data_ingestion_config.raw_data_filepath
            os.makedirs(output_dir, exist_ok=True)
            
            df.to_csv(output_filepath, index=False)
            logging.info(f"Saved raw data snapshot to artifacts: {output_filepath}")

            logging.info("Exited initiate_data_ingestion method.")
            
            return self.data_ingestion_config.raw_data_dir

        except Exception as e:
            raise CustomException(e, sys) from e