import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_curve, auc
from sklearn.utils.class_weight import compute_class_weight
import joblib
from base_model import BaseModel


class LogRegModel(BaseModel):
    def __init__(self, file_path, train_start, train_end, test_start, test_end):
        super().__init__(file_path, train_start, train_end, test_start, test_end)
        # Elastic Net parameters
        l1_ratio = 0.5  # L1 weight in the range [0,1]. 0 is L2, 1 is L1.
        alpha = 1.0     # Regularization strength. Higher values mean more regularization.
        self.model = LogisticRegression(class_weight='balanced', penalty='elasticnet', l1_ratio=l1_ratio, C=1/alpha, solver='saga', max_iter=1000)

    def train(self):
        self.train_test_split_time_series()

        print("y_train value counts: ", self.y_train.value_counts())
        # self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        # self.X_test_scaled = self.scaler.transform(self.X_test)

        # self.model.fit(self.X_train_scaled, self.y_train)
        print("check X train: ", self.X_train)
        print("check y train: ", self.y_train)
        self.model.fit(self.X_train, self.y_train)

        # Save the model to a file
        joblib.dump(self.model, 'logistic_regression_model.pkl')
        print("Model saved to logistic_regression_model.pkl")


    def predict(self):
        # self.data['PredictedLabel'] = self.model.predict(self.scaler.transform(self.X))
        # return self.data
        # predicted_categories = self.model.predict(self.scaler.transform(self.X_test_scaled))
        print("X_test shape: ", self.X_test.shape)
        # X_test shape:  (11520, 13)
        predicted_categories = self.model.predict(self.X_test)
        # print("CHECK predicted_labels: ", predicted_categories)
        return predicted_categories

    def evaluate(self, X, y):
        # Implement evaluation logic
        pass


