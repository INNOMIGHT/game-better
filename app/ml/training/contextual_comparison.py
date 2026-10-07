from pathlib import Path

import pandas as pd

from sklearn.linear_model import (
    LogisticRegression,
)

from sklearn.model_selection import (
    StratifiedKFold,
)

from sklearn.pipeline import Pipeline

from sklearn.preprocessing import (
    StandardScaler,
)

from app.ml.training.baseline import (
    evaluate_model,
)


DATASET_PATH = Path(
    "artifacts/ml002/"
    "ml002_contextual_dataset.csv"
)


BASIC_FEATURES = [
    "gold_difference_at_10",
    "xp_difference_at_10",
    "cs_difference_at_10",
    "level_difference_at_10",
]


CONTEXTUAL_FEATURES = [
    "kill_difference_before_10",
    "assist_difference_before_10",

    "objective_participation_difference_before_10",
    "dragon_participation_difference_before_10",
    "building_participation_difference_before_10",
    "plate_participation_difference_before_10",

    "cs_rate_difference_before_10",
    "gold_rate_difference_before_10",
    "xp_rate_difference_before_10",
]


TARGET_COLUMN = "team_100_win"


def create_logistic_model():

    return Pipeline([
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


def print_results(
    title,
    results,
):

    print()
    print(title)
    print(
        "=" * len(title)
    )

    print(
        f"Accuracy: "
        f"{results['mean_accuracy']:.3f}"
    )

    print(
        f"ROC-AUC: "
        f"{results['mean_roc_auc']:.3f}"
    )

    print(
        f"Log loss: "
        f"{results['mean_log_loss']:.3f}"
    )


def run_contextual_comparison():

    df = pd.read_csv(
        DATASET_PATH
    )

    y = df[
        TARGET_COLUMN
    ]

    # EXACT same CV configuration
    # as ML_001.
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    # ----------------------------------
    # ML_001
    # ----------------------------------

    X_basic = df[
        BASIC_FEATURES
    ]

    basic_results = evaluate_model(
        model=create_logistic_model(),
        X=X_basic,
        y=y,
        cv=cv,
        model_name="ML_001 Basic",
    )

    # ----------------------------------
    # ML_002
    # ----------------------------------

    enhanced_features = (
        BASIC_FEATURES
        + CONTEXTUAL_FEATURES
    )

    X_contextual = df[
        enhanced_features
    ]

    contextual_results = evaluate_model(
        model=create_logistic_model(),
        X=X_contextual,
        y=y,
        cv=cv,
        model_name="ML_002 Contextual",
    )

    print()
    print(
        "GAMEBETTER ML_001 VS ML_002"
    )

    print(
        "============================"
    )

    print(
        f"Matches: {len(df)}"
    )

    print_results(
        "ML_001 BASIC",
        basic_results,
    )

    print_results(
        "ML_002 CONTEXTUAL",
        contextual_results,
    )

    auc_change = (
        contextual_results[
            "mean_roc_auc"
        ]
        - basic_results[
            "mean_roc_auc"
        ]
    )

    accuracy_change = (
        contextual_results[
            "mean_accuracy"
        ]
        - basic_results[
            "mean_accuracy"
        ]
    )

    loss_change = (
        contextual_results[
            "mean_log_loss"
        ]
        - basic_results[
            "mean_log_loss"
        ]
    )

    print()
    print("CHANGE")
    print("======")

    print(
        f"AUC: "
        f"{auc_change:+.3f}"
    )

    print(
        f"Accuracy: "
        f"{accuracy_change:+.3f}"
    )

    print(
        f"Log loss: "
        f"{loss_change:+.3f}"
    )

    print()
    print("ML_002 FOLDS")
    print("============")

    for fold in contextual_results[
        "folds"
    ]:

        print(
            f"Fold {fold['fold']}: "
            f"accuracy="
            f"{fold['accuracy']:.3f}, "
            f"auc="
            f"{fold['roc_auc']:.3f}, "
            f"log_loss="
            f"{fold['log_loss']:.3f}"
        )

    return {
        "basic":
            basic_results,

        "contextual":
            contextual_results,
    }