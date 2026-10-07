from pathlib import Path

import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    log_loss,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


DATASET_PATH = Path(
    "artifacts/ml001/ml001_match_dataset.csv"
)

FEATURE_COLUMNS = [
    "gold_difference_at_10",
    "xp_difference_at_10",
    "cs_difference_at_10",
    "level_difference_at_10",
]

TARGET_COLUMN = "team_100_win"


def evaluate_model(
    model,
    X,
    y,
    cv,
    model_name,
):
    fold_results = []

    for fold_number, (train_index, test_index) in enumerate(
        cv.split(X, y),
        start=1,
    ):
        X_train = X.iloc[train_index]
        X_test = X.iloc[test_index]

        y_train = y.iloc[train_index]
        y_test = y.iloc[test_index]

        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(
            X_test
        )

        probabilities = model.predict_proba(
            X_test
        )[:, 1]

        accuracy = accuracy_score(
            y_test,
            predictions,
        )

        try:
            auc = roc_auc_score(
                y_test,
                probabilities,
            )
        except ValueError:
            auc = None

        loss = log_loss(
            y_test,
            probabilities,
            labels=[0, 1],
        )

        result = {
            "fold": fold_number,
            "accuracy": accuracy,
            "roc_auc": auc,
            "log_loss": loss,
        }

        fold_results.append(result)

    valid_auc_values = [
        result["roc_auc"]
        for result in fold_results
        if result["roc_auc"] is not None
    ]

    summary = {
        "model": model_name,

        "mean_accuracy":
            sum(
                result["accuracy"]
                for result in fold_results
            )
            / len(fold_results),

        "mean_roc_auc":
            (
                sum(valid_auc_values)
                / len(valid_auc_values)
                if valid_auc_values
                else None
            ),

        "mean_log_loss":
            sum(
                result["log_loss"]
                for result in fold_results
            )
            / len(fold_results),

        "folds": fold_results,
    }

    return summary


def run_baselines():

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: "
            f"{DATASET_PATH}"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    X = df[
        FEATURE_COLUMNS
    ]

    y = df[
        TARGET_COLUMN
    ]

    print()
    print("ML_001 BASELINE")
    print("================")

    print(
        f"Matches: {len(df)}"
    )

    print(
        f"Features: "
        f"{FEATURE_COLUMNS}"
    )

    print(
        f"Positive class: "
        f"{int(y.sum())}"
    )

    print(
        f"Negative class: "
        f"{int((y == 0).sum())}"
    )

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    dummy_model = DummyClassifier(
        strategy="prior",
    )

    logistic_model = Pipeline([
        (
            "scaler",
            StandardScaler(),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                random_state=42,
            ),
        ),
    ])

    dummy_results = evaluate_model(
        model=dummy_model,
        X=X,
        y=y,
        cv=cv,
        model_name="DummyClassifier",
    )

    logistic_results = evaluate_model(
        model=logistic_model,
        X=X,
        y=y,
        cv=cv,
        model_name="LogisticRegression",
    )

    print()
    print("DUMMY CLASSIFIER")
    print("================")

    print(
        f"Mean accuracy: "
        f"{dummy_results['mean_accuracy']:.3f}"
    )

    print(
        f"Mean ROC-AUC: "
        f"{dummy_results['mean_roc_auc']:.3f}"
    )

    print(
        f"Mean log loss: "
        f"{dummy_results['mean_log_loss']:.3f}"
    )

    print()
    print("LOGISTIC REGRESSION")
    print("===================")

    print(
        f"Mean accuracy: "
        f"{logistic_results['mean_accuracy']:.3f}"
    )

    print(
        f"Mean ROC-AUC: "
        f"{logistic_results['mean_roc_auc']:.3f}"
    )

    print(
        f"Mean log loss: "
        f"{logistic_results['mean_log_loss']:.3f}"
    )

    print()
    print("LOGISTIC FOLDS")
    print("==============")

    for fold in logistic_results["folds"]:

        print(
            f"Fold {fold['fold']}: "
            f"accuracy="
            f"{fold['accuracy']:.3f}, "
            f"auc="
            f"{fold['roc_auc']:.3f}, "
            f"log_loss="
            f"{fold['log_loss']:.3f}"
        )

    final_logistic_model = Pipeline([
        (
            "scaler",
            StandardScaler(),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                random_state=42,
            ),
        ),
    ])

    final_logistic_model.fit(
        X,
        y,
    )

    classifier = (
        final_logistic_model
        .named_steps["classifier"]
    )

    coefficients = (
        classifier.coef_[0]
    )

    print()
    print("LEARNED FEATURE WEIGHTS")
    print("=======================")

    feature_weights = sorted(
        zip(
            FEATURE_COLUMNS,
            coefficients,
        ),
        key=lambda item: abs(item[1]),
        reverse=True,
    )

    for feature, weight in feature_weights:
        direction = (
            "Team 100 win"
            if weight > 0
            else "Team 200 win"
        )

        print(
            f"{feature}: "
            f"{weight:.4f} "
            f"-> {direction}"
        )

    return {
        "dummy": dummy_results,
        "logistic": logistic_results,
    }