import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import RandomOverSampler
from src.constant import *
from src.exception import CustomException
from src.logger import logging
from src.utils.main_utils import MainUtils
from dataclasses import dataclass

@dataclass
class DataTransformationConfig:
    data_transformation_dir = os.path.join(artifact_folder, 'data_transformation')
    transformed_train_file_path = os.path.join(data_transformation_dir, 'train.npy')
    transformed_test_file_path = os.path.join(data_transformation_dir, 'test.npy')
    transformed_object_file_path = os.path.join(data_transformation_dir, 'preprocessor.pkl')

class DataTransformation:
    def __init__(self, valid_data_dir):
        self.valid_data_dir = valid_data_dir
        self.data_transformation_config = DataTransformationConfig()
        self.utils = MainUtils()

    def get_validated_data(self) -> pd.DataFrame:
        try:
            validated_data_path = os.path.join(self.valid_data_dir, 'validated_data.csv')
            df = pd.read_csv(validated_data_path)
            logging.info(f"Loaded validated data from: {validated_data_path}")
            return df
        except Exception as e:
            raise CustomException(e, sys)

    def get_data_preprocessor_object(self):
        try:
            preprocessor = SimpleImputer(strategy='most_frequent')
            return preprocessor
        except Exception as e:
            raise CustomException(e, sys)

    def initiate_data_transformation(self):
        logging.info("Entered initiate_data_transformation method.")
        try:
            dataframe = self.get_validated_data()
            
            dataframe = self.utils.remove_unwanted_spaces(dataframe)
            dataframe.replace('?', np.nan, inplace=True)

            X = dataframe.drop(columns=TARGET_COLUMN)
            y = np.where(dataframe[TARGET_COLUMN] == -1, 0, 1)

            sampler = RandomOverSampler(random_state=42)
            x_sampled, y_sampled = sampler.fit_resample(X, y)

            X_train, X_test, y_train, y_test = train_test_split(x_sampled, y_sampled, test_size=0.2, random_state=42)

            preprocessor = self.get_data_preprocessor_object()
            
            preprocessor.fit(X_train)

            x_train_scaled = preprocessor.transform(X_train)
            x_test_scaled = preprocessor.transform(X_test)
            
            preprocessor_path = self.data_transformation_config.transformed_object_file_path
            os.makedirs(os.path.dirname(preprocessor_path), exist_ok=True)
            self.utils.save_object(file_path=preprocessor_path, obj=preprocessor)
            logging.info(f"Saved preprocessor object to: {preprocessor_path}")

            return x_train_scaled, y_train, x_test_scaled, y_test, preprocessor_path

        except Exception as e:
            raise CustomException(e, sys) from e