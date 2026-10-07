from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.base import clone

from sklearn.dummy import DummyClassifier

from sklearn.linear_model import (
    LogisticRegression,
)

from sklearn.metrics import (
    accuracy_score,
    log_loss,
    roc_auc_score,
)

from sklearn.model_selection import (
    StratifiedGroupKFold,
)

from sklearn.pipeline import Pipeline

from sklearn.preprocessing import (
    StandardScaler,
)


DATASET_PATH = Path(
    "artifacts/ml_farm/"
    "farm_recovery_dataset.csv"
)


TARGET_COLUMN = "recovered"

GROUP_COLUMN = "match_id"


FEATURE_COLUMNS = [

    # ----------------------------------
    # When did disruption happen?
    # ----------------------------------

    "disruption_minute",
    "level_at_disruption",

    # ----------------------------------
    # Farming state
    # ----------------------------------

    "baseline_cs_per_min",
    "observed_cs_per_min",
    "relative_cs_drop",

    # ----------------------------------
    # Economic context
    # ----------------------------------

    "baseline_gold_per_min",
    "current_gold_per_min",
    "gold_rate_change",

    "baseline_xp_per_min",
    "current_xp_per_min",
    "xp_rate_change",

    # ----------------------------------
    # Events DURING disruption
    # ----------------------------------

    "kills_during_disruption",
    "deaths_during_disruption",
    "assists_during_disruption",
    "objectives_during_disruption",

    # ----------------------------------
    # Events immediately BEFORE it
    # ----------------------------------

    "recent_kills",
    "recent_deaths",
    "recent_assists",
    "recent_objectives",
]


def create_logistic_model():

    return Pipeline([
        (
            "scaler",
            StandardScaler(),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                random_state=42,
            ),
        ),
    ])


def evaluate_grouped_model(
    model,
    X,
    y,
    groups,
):

    cv = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    folds = []

    for fold_number, (
        train_index,
        test_index,
    ) in enumerate(
        cv.split(
            X,
            y,
            groups=groups,
        ),
        start=1,
    ):

        X_train = X.iloc[
            train_index
        ]

        X_test = X.iloc[
            test_index
        ]

        y_train = y.iloc[
            train_index
        ]

        y_test = y.iloc[
            test_index
        ]

        train_groups = groups.iloc[
            train_index
        ]

        test_groups = groups.iloc[
            test_index
        ]

        # ----------------------------------
        # Critical leakage assertion
        # ----------------------------------

        overlap = (
            set(train_groups)
            & set(test_groups)
        )

        if overlap:

            raise RuntimeError(
                "MATCH LEAKAGE DETECTED: "
                f"{len(overlap)} matches "
                "exist in both train and test."
            )

        fold_model = clone(
            model
        )

        fold_model.fit(
            X_train,
            y_train,
        )

        predictions = (
            fold_model.predict(
                X_test
            )
        )

        probabilities = (
            fold_model.predict_proba(
                X_test
            )[:, 1]
        )

        accuracy = accuracy_score(
            y_test,
            predictions,
        )

        auc = roc_auc_score(
            y_test,
            probabilities,
        )

        loss = log_loss(
            y_test,
            probabilities,
            labels=[0, 1],
        )

        folds.append({
            "fold":
                fold_number,

            "accuracy":
                accuracy,

            "roc_auc":
                auc,

            "log_loss":
                loss,

            "train_samples":
                len(train_index),

            "test_samples":
                len(test_index),

            "train_matches":
                train_groups.nunique(),

            "test_matches":
                test_groups.nunique(),

            "test_recovery_rate":
                float(
                    y_test.mean()
                ),
        })

    return {
        "mean_accuracy":
            float(
                np.mean([
                    fold["accuracy"]
                    for fold in folds
                ])
            ),

        "mean_roc_auc":
            float(
                np.mean([
                    fold["roc_auc"]
                    for fold in folds
                ])
            ),

        "mean_log_loss":
            float(
                np.mean([
                    fold["log_loss"]
                    for fold in folds
                ])
            ),

        "folds":
            folds,
    }


def print_results(
    title,
    results,
):

    print()
    print(title)
    print("=" * len(title))

    print(
        f"Mean accuracy: "
        f"{results['mean_accuracy']:.3f}"
    )

    print(
        f"Mean ROC-AUC: "
        f"{results['mean_roc_auc']:.3f}"
    )

    print(
        f"Mean log loss: "
        f"{results['mean_log_loss']:.3f}"
    )

    print()
    print("Folds")
    print("-----")

    for fold in results["folds"]:

        print(
            f"Fold {fold['fold']}: "
            f"accuracy="
            f"{fold['accuracy']:.3f}, "
            f"auc="
            f"{fold['roc_auc']:.3f}, "
            f"log_loss="
            f"{fold['log_loss']:.3f}, "
            f"train_matches="
            f"{fold['train_matches']}, "
            f"test_matches="
            f"{fold['test_matches']}, "
            f"test_samples="
            f"{fold['test_samples']}, "
            f"recovery_rate="
            f"{fold['test_recovery_rate']:.3f}"
        )


def run_farm_recovery_baseline():

    if not DATASET_PATH.exists():

        raise FileNotFoundError(
            f"Dataset not found: "
            f"{DATASET_PATH}"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    # ----------------------------------
    # Validate required columns
    # ----------------------------------

    required_columns = (
        FEATURE_COLUMNS
        + [
            TARGET_COLUMN,
            GROUP_COLUMN,
        ]
    )

    missing_columns = [
        column
        for column
        in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise RuntimeError(
            "Dataset is missing columns: "
            f"{missing_columns}"
        )

    X = df[
        FEATURE_COLUMNS
    ]

    y = df[
        TARGET_COLUMN
    ].astype(int)

    groups = df[
        GROUP_COLUMN
    ]

    print()
    print(
        "ML_FARM_001 RECOVERY BASELINE"
    )
    print(
        "============================="
    )

    print(
        f"Disruption samples: "
        f"{len(df)}"
    )

    print(
        f"Unique matches: "
        f"{groups.nunique()}"
    )

    print(
        f"Features: "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        f"Recovered: "
        f"{int(y.sum())}"
    )

    print(
        f"Not recovered: "
        f"{len(y) - int(y.sum())}"
    )

    print(
        f"Recovery rate: "
        f"{y.mean():.3f}"
    )

    # ==================================
    # Dummy baseline
    # ==================================

    dummy_model = DummyClassifier(
        strategy="prior",
    )

    dummy_results = (
        evaluate_grouped_model(
            model=dummy_model,
            X=X,
            y=y,
            groups=groups,
        )
    )

    # ==================================
    # Logistic Regression
    # ==================================

    logistic_model = (
        create_logistic_model()
    )

    logistic_results = (
        evaluate_grouped_model(
            model=logistic_model,
            X=X,
            y=y,
            groups=groups,
        )
    )

    print_results(
        "DUMMY CLASSIFIER",
        dummy_results,
    )

    print_results(
        "LOGISTIC REGRESSION",
        logistic_results,
    )

    print()
    print(
        "IMPROVEMENT OVER DUMMY"
    )
    print(
        "======================"
    )

    print(
        f"Accuracy: "
        f"{logistic_results['mean_accuracy'] - dummy_results['mean_accuracy']:+.3f}"
    )

    print(
        f"ROC-AUC: "
        f"{logistic_results['mean_roc_auc'] - dummy_results['mean_roc_auc']:+.3f}"
    )

    print(
        f"Log loss: "
        f"{logistic_results['mean_log_loss'] - dummy_results['mean_log_loss']:+.3f}"
    )
    # ==================================
    # Exploratory full-data fit
    #
    # This is ONLY for coefficient
    # inspection, NOT performance.
    # ==================================

    final_model = (
        create_logistic_model()
    )

    final_model.fit(
        X,
        y,
    )

    classifier = (
        final_model
        .named_steps[
            "classifier"
        ]
    )

    coefficients = (
        classifier.coef_[0]
    )

    feature_weights = sorted(
        zip(
            FEATURE_COLUMNS,
            coefficients,
        ),
        key=lambda item:
            abs(item[1]),
        reverse=True,
    )

    print()
    print(
        "LEARNED FEATURE WEIGHTS"
    )
    print(
        "======================="
    )

    for feature, weight in feature_weights:

        direction = (
            "more likely recovery"
            if weight > 0
            else "less likely recovery"
        )

        print(
            f"{feature}: "
            f"{weight:+.4f} "
            f"-> {direction}"
        )

    return {
        "dummy":
            dummy_results,

        "logistic":
            logistic_results,
    }