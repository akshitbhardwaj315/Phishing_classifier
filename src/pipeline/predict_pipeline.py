# src/pipeline/predict_pipeline.py

import os
import sys
import pandas as pd
from src.logger import logging
from src.exception import CustomException
from src.constant import *
from src.utils.main_utils import MainUtils

class PredictionPipeline:
    def __init__(self):
        logging.info("Initializing PredictionPipeline...")
        self.utils = MainUtils()
        self.model = self._load_model()
        
    def _load_model(self) -> object:
        try:
            local_model_path = "model.pkl"

            if os.path.exists(local_model_path):
                logging.info(f"Loading model from local path: {local_model_path}")
                model = self.utils.load_object(file_path=local_model_path)
                logging.info("Model loaded successfully.")
                return model
            else:
                logging.error(f"Model file not found at {local_model_path}")
                raise FileNotFoundError(f"Model file not found at {local_model_path}")

        except Exception as e:
            logging.critical(f"Failed to load model: {e}")
            raise CustomException(e, sys)

    def predict(self, input_data: pd.DataFrame) -> pd.DataFrame:
        try:
            logging.info(f"Running prediction on {input_data.shape[0]} records.")
            
            data_to_predict = input_data.copy()
            
            if TARGET_COLUMN in data_to_predict.columns:
                logging.info(f"Removing target column '{TARGET_COLUMN}' from input data")
                data_to_predict = data_to_predict.drop(columns=[TARGET_COLUMN])
            if 'Result' in data_to_predict.columns:
                logging.info("Removing 'Result' column from input data")
                data_to_predict = data_to_predict.drop(columns=['Result'])
            
            predictions = self.model.predict(data_to_predict)
            
            result_df = input_data.copy()
            
            target_column_mapping = {0: 'phishing', 1: 'safe'}
            result_df['Result'] = [target_column_mapping.get(pred, 'unknown') for pred in predictions]
            result_df['Result_Value'] = predictions

            logging.info("Prediction completed successfully.")
            return result_df

        except Exception as e:
            raise CustomException(e, sys)