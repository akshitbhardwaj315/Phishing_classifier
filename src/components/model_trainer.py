import sys
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from src.constant import *
from src.exception import CustomException
from src.logger import logging
from src.utils.main_utils import MainUtils
from dataclasses import dataclass

@dataclass
class ModelTrainerConfig:
    model_trainer_dir = os.path.join(artifact_folder, 'model_trainer')
    trained_model_path = "model.pkl" 
    expected_accuracy = 0.75
    model_config_file_path = os.path.join('config', 'model.yaml')

class ModelTrainer:
    def __init__(self):
        self.model_trainer_config = ModelTrainerConfig()
        self.utils = MainUtils()
        self.models = {
            "GaussianNB": GaussianNB(),
            "XGBClassifier": XGBClassifier(objective='binary:logistic', random_state=42),
            "LogisticRegression": LogisticRegression(random_state=42)
        }

    def evaluate_models(self, X_train, y_train, X_test, y_test, models):
        try:
            report = {}
            for model_name, model in models.items():
                model.fit(X_train, y_train)
                y_test_pred = model.predict(X_test)
                test_model_score = accuracy_score(y_test, y_test_pred)
                report[model_name] = test_model_score
            return report
        except Exception as e:
            raise CustomException(e, sys)

    def get_best_model(self, X_train, y_train, X_test, y_test):
        try:
            model_report = self.evaluate_models(
                X_train=X_train, y_train=y_train, 
                X_test=X_test, y_test=y_test,
                models=self.models
            )
            logging.info(f"Model evaluation report: {model_report}")

            best_model_score = max(sorted(model_report.values()))
            best_model_name = list(model_report.keys())[
                list(model_report.values()).index(best_model_score)
            ]
            best_model_object = self.models[best_model_name]
            
            logging.info(f"Best model found: {best_model_name} with score {best_model_score}")
            return best_model_name, best_model_object, best_model_score
        except Exception as e:
            raise CustomException(e, sys)

    def finetune_best_model(self, best_model_object, best_model_name, X_train, y_train):
        try:
            model_param_grid = self.utils.read_yaml_file(
                self.model_trainer_config.model_config_file_path
            )["model_selection"]["model"][best_model_name]["search_param_grid"]

            grid_search = GridSearchCV(
                best_model_object, param_grid=model_param_grid, cv=5, n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            
            best_params = grid_search.best_params_
            logging.info(f"Best params for {best_model_name}: {best_params}")

            finetuned_model = best_model_object.set_params(**best_params)
            return finetuned_model
        except Exception as e:
            raise CustomException(e, sys)

    def initiate_model_trainer(self, x_train, y_train, x_test, y_test, preprocessor_path):
        try:
            logging.info("Finding best model...")
            best_model_name, best_model, best_model_score = self.get_best_model(
                X_train=x_train, y_train=y_train,
                X_test=x_test, y_test=y_test
            )
            
            logging.info("Finetuning best model...")
            finetuned_model = self.finetune_best_model(
                best_model_object=best_model,
                best_model_name=best_model_name,
                X_train=x_train,
                y_train=y_train
            )

            logging.info("Loading preprocessor object...")
            preprocessor = self.utils.load_object(file_path=preprocessor_path)

            final_model_pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('model', finetuned_model)
            ])

            final_model_pipeline.fit(x_train, y_train)
            y_pred = final_model_pipeline.predict(x_test)
            final_model_score = accuracy_score(y_test, y_pred)
            
            logging.info(f"Final finetuned model: {best_model_name}, Score: {final_model_score}")

            if final_model_score < self.model_trainer_config.expected_accuracy:
                raise Exception(f"Final model accuracy ({final_model_score}) is less than expected ({self.model_trainer_config.expected_accuracy})")
            
            model_path = self.model_trainer_config.trained_model_path
            
            self.utils.save_object(
                file_path=model_path,
                obj=final_model_pipeline,
            )
            logging.info(f"Saved final model pipeline to: {model_path}")
            
            return final_model_score
        except Exception as e:
            raise CustomException(e, sys)