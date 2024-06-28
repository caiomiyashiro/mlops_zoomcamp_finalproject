# pylint: disable=invalid-name,missing-module-docstring,import-error,wrong-import-position,no-name-in-module

import os
import sys

import numpy as np
import pandas as pd
from dotenv import find_dotenv, load_dotenv
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

import mlflow

# adding parent folder to sys.path to use utils folder functions
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
from utils.dataset import get_dataset_ucirepo

dotenv_path = find_dotenv(filename=".env", raise_error_if_not_found=True, usecwd=True)
load_dotenv(dotenv_path, override=True)  # Load variables from .env file

MLFLOW_EXPERIMENT_NAME = os.environ.get(
    "MLFLOW_EXPERIMENT_NAME", "wine_quality_hyperparameter_optimization"
)
MLFLOW_TRACKING_URL = os.environ.get("MLFLOW_TRACKING_URL", "http://127.0.0.1:5001")
print(f"--- Loaded MLFLOW_EXPERIMENT_NAME: {MLFLOW_EXPERIMENT_NAME}")
print(f"--- Loaded MLFLOW_TRACKING_URL: {MLFLOW_TRACKING_URL}")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URL)
mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
mlflow.sklearn.autolog()


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
) -> DecisionTreeRegressor:
    """
    Trains a Decision Tree model on the given features and targets.
    Parameters:
        X_train (pd.DataFrame): The features of the training set.
        y_train (pd.DataFrame): The targets of the training set.
        X_val (pd.DataFrame): The features of the validation set.
        y_val (pd.DataFrame): The targets of the validation set.
    Returns:
        final_model (DecisionTreeRegressor): The trained Decision Tree model.
    """
    # Split the data

    # Define the hyperparameter search space
    space = {
        "criterion": hp.choice(
            "criterion", ["squared_error", "friedman_mse", "absolute_error", "poisson"]
        ),
        "splitter": hp.choice("splitter", ["best", "random"]),
        "max_depth": hp.choice("max_depth", [None] + list(range(1, 21))),
        "min_samples_split": hp.choice(
            "min_samples_split", range(2, 21)
        ),  # Integer values from 2 to 20
        "min_samples_leaf": hp.choice(
            "min_samples_leaf", range(1, 21)
        ),  # Integer values from 1 to 20
        # "min_weight_fraction_leaf": hp.uniform("min_weight_fraction_leaf", 0.0, 0.5),
        "max_features": hp.choice(
            "max_features", [None, "sqrt", "log2"] + list(np.arange(0.1, 1.1, 0.1))
        ),
        "max_leaf_nodes": hp.choice("max_leaf_nodes", [None] + list(range(2, 101))),
        # "min_impurity_decrease": hp.uniform("min_impurity_decrease", 0.0, 1.0),
        # "ccp_alpha": hp.uniform("ccp_alpha", 0.0, 1.0),
    }

    # space = {
    #     'criterion': hp.choice('criterion', ['gini', 'entropy', 'log_loss']),
    #     'splitter': hp.choice('splitter', ['best', 'random']),
    #     'max_depth': hp.choice('max_depth', [
    #         None,
    #         hp.randint('max_depth_int', 1, 51)  # randint is exclusive on upper bound
    #     ]),
    #     'min_samples_split': hp.randint('min_samples_split', 2, 21),
    #     'min_samples_leaf': hp.randint('min_samples_leaf', 1, 21),
    #     'min_weight_fraction_leaf': hp.uniform('min_weight_fraction_leaf', 0.0, 0.5),
    #     'max_features': hp.choice('max_features', [
    #         None,
    #         'sqrt',
    #         'log2',
    #         hp.uniform('max_features_float', 0.1, 1.0)
    #     ]),
    #     'random_state': hp.choice('random_state', [
    #         None,
    #         hp.randint('random_state_int', 1000)
    #     ]),
    #     'max_leaf_nodes': hp.choice('max_leaf_nodes', [
    #         None,
    #         hp.randint('max_leaf_nodes_int', 2, 101)  # randint is exclusive on upper bound
    #     ]),
    #     'min_impurity_decrease': hp.uniform('min_impurity_decrease', 0.0, 0.2),
    #     'class_weight': hp.choice('class_weight', [
    #         None,
    #         'balanced',
    #         {0: hp.uniform('weight_class_0', 0.1, 10), 1: hp.uniform('weight_class_1', 0.1, 10)},
    #         {0: hp.uniform('weight_class_0_alt', 0.1, 10), 1: 1.0},
    #     ]),
    #     'ccp_alpha': hp.uniform('ccp_alpha', 0.0, 0.05)
    # }

    # Define the objective function
    def objective(params):
        with mlflow.start_run():
            # Create the model with the given hyperparameters
            model = DecisionTreeRegressor(**params)
            # model = DecisionTreeClassifier(**params)
            model.fit(X_train, y_train)
            y_val_pred = model.predict(X_val)
            print(params)
            print(np.unique(y_val_pred, return_counts=True))
            print("----------------------------")
            mse = mean_squared_error(y_val, y_val_pred)
            mlflow.sklearn.log_model(model, artifact_path="artifacts")
        # Return the loss (negative score)
        return {"loss": mse, "status": STATUS_OK}

    # Perform hyperparameter optimization
    trials = Trials()
    _ = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=100, trials=trials)


def main():
    # pylint: disable=missing-function-docstring
    # Fetch the dataset
    X, y = get_dataset_ucirepo()

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train the model
    train_model(X_train, y_train, X_test, y_test)


if __name__ == "__main__":
    main()
