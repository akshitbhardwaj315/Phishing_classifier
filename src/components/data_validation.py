import sys
import os
import pandas as pd
import json
from pathlib import Path
from src.constant import *
from src.exception import CustomException
from src.logger import logging
from src.utils.main_utils import MainUtils
from dataclasses import dataclass

@dataclass
class DataValidationConfig:
    data_validation_dir: str = os.path.join(artifact_folder, 'data_validation')
    valid_data_dir: str = os.path.join(data_validation_dir, 'validated')
    invalid_data_dir: str = os.path.join(data_validation_dir, 'invalid')
    validated_data_filepath: str = os.path.join(valid_data_dir, 'validated_data.csv')
    schema_config_file_path: str = os.path.join('config', 'training_schema.json')

class DataValidation:
    def __init__(self, raw_data_store_dir: Path):
        self.raw_data_store_dir = raw_data_store_dir
        self.data_validation_config = DataValidationConfig()
        self.utils = MainUtils()
        
    def get_schema_columns(self) -> dict:
        try:
            with open(self.data_validation_config.schema_config_file_path, 'r') as f:
                schema = json.load(f)
            return schema['ColName']
        except Exception as e:
            raise CustomException(e, sys)
            
    def validate_data_schema(self) -> str:
        logging.info("Starting data schema validation.")
        try:
            schema_columns = self.get_schema_columns()
            expected_columns = list(schema_columns.keys())
            
            # Use the single data.csv from data_ingestion
            raw_data_filepath = os.path.join(self.raw_data_store_dir, 'data.csv')
            
            if not os.path.exists(raw_data_filepath):
                raise FileNotFoundError(f"Raw data file not found at: {raw_data_filepath}")
                
            df = pd.read_csv(raw_data_filepath)
            
            actual_columns = list(df.columns)
            
            if len(actual_columns) != len(expected_columns):
                raise Exception(f"Schema mismatch: Expected {len(expected_columns)} columns, but got {len(actual_columns)}")
            
            missing_columns = [col for col in expected_columns if col not in actual_columns]
            if missing_columns:
                raise Exception(f"Schema mismatch: Missing columns: {missing_columns}")

            logging.info(f"Data schema validated successfully. Shape: {df.shape}")
            
            # Save the validated data
            os.makedirs(self.data_validation_config.valid_data_dir, exist_ok=True)
            validated_filepath = self.data_validation_config.validated_data_filepath
            df.to_csv(validated_filepath, index=False)
            logging.info(f"Validated data saved to: {validated_filepath}")

            return self.data_validation_config.valid_data_dir

        except Exception as e:
            raise CustomException(e, sys)

    def initiate_data_validation(self):
        logging.info("Entered initiate_data_validation method.")
        try:
            logging.info("Initiating data schema validation.")
            valid_data_dir = self.validate_data_schema()
            logging.info("Data validation completed.")
            return valid_data_dir
        except Exception as e:
            raise CustomException(e, sys) from e