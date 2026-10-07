from pathlib import Path

import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.training.baseline import evaluate_model


DATASET_PATH = Path(
    "artifacts/ml002/"
    "ml002b_farming_disruption_dataset.csv"
)


# --------------------------------------------------
# ML_001
# Basic minute-10 snapshot features
# --------------------------------------------------

BASIC_FEATURES = [
    "gold_difference_at_10",
    "xp_difference_at_10",
    "cs_difference_at_10",
    "level_difference_at_10",
]


# --------------------------------------------------
# ML_002A
# Contextual / temporal features
# --------------------------------------------------

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


# --------------------------------------------------
# ML_002B
# Farming disruption features
# --------------------------------------------------

FARM_DISRUPTION_FEATURES = [
    "farm_disruption_count_difference",
    "farm_mean_drop_difference",
    "farm_max_drop_difference",
    "farm_recovered_difference",
    "farm_not_recovered_difference",
    "farm_combat_disruption_difference",
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
    print("=" * len(title))

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


def print_change(
    title,
    old_results,
    new_results,
):

    auc_change = (
        new_results["mean_roc_auc"]
        - old_results["mean_roc_auc"]
    )

    accuracy_change = (
        new_results["mean_accuracy"]
        - old_results["mean_accuracy"]
    )

    loss_change = (
        new_results["mean_log_loss"]
        - old_results["mean_log_loss"]
    )

    print()
    print(title)
    print("=" * len(title))

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


def run_disruption_comparison():

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: "
            f"{DATASET_PATH}"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    y = df[
        TARGET_COLUMN
    ]

    # --------------------------------------------------
    # EXACT SAME CV CONFIGURATION FOR ALL EXPERIMENTS
    # --------------------------------------------------

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    # ==================================================
    # ML_001
    # ==================================================

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

    # ==================================================
    # ML_002A
    # Basic + contextual
    # ==================================================

    contextual_feature_set = (
        BASIC_FEATURES
        + CONTEXTUAL_FEATURES
    )

    X_contextual = df[
        contextual_feature_set
    ]

    contextual_results = evaluate_model(
        model=create_logistic_model(),
        X=X_contextual,
        y=y,
        cv=cv,
        model_name="ML_002A Contextual",
    )

    # ==================================================
    # ML_002B
    # Basic + contextual + farming disruption
    # ==================================================

    disruption_feature_set = (
        BASIC_FEATURES
        + CONTEXTUAL_FEATURES
        + FARM_DISRUPTION_FEATURES
    )

    X_disruption = df[
        disruption_feature_set
    ]

    disruption_results = evaluate_model(
        model=create_logistic_model(),
        X=X_disruption,
        y=y,
        cv=cv,
        model_name="ML_002B Farming Disruption",
    )

    # ==================================================
    # OUTPUT
    # ==================================================

    print()
    print(
        "GAMEBETTER ML EXPERIMENT COMPARISON"
    )
    print(
        "==================================="
    )

    print(
        f"Matches: {len(df)}"
    )

    print(
        f"ML_001 feature count: "
        f"{len(BASIC_FEATURES)}"
    )

    print(
        f"ML_002A feature count: "
        f"{len(contextual_feature_set)}"
    )

    print(
        f"ML_002B feature count: "
        f"{len(disruption_feature_set)}"
    )

    print_results(
        "ML_001 BASIC",
        basic_results,
    )

    print_results(
        "ML_002A CONTEXTUAL",
        contextual_results,
    )

    print_results(
        "ML_002B + FARM DISRUPTION",
        disruption_results,
    )

    # --------------------------------------------------
    # Incremental changes
    # --------------------------------------------------

    print_change(
        "CHANGE: ML_001 -> ML_002A",
        basic_results,
        contextual_results,
    )

    print_change(
        "CHANGE: ML_002A -> ML_002B",
        contextual_results,
        disruption_results,
    )

    print_change(
        "TOTAL CHANGE: ML_001 -> ML_002B",
        basic_results,
        disruption_results,
    )

    # --------------------------------------------------
    # ML_002B fold details
    # --------------------------------------------------

    print()
    print("ML_002B FOLDS")
    print("=============")

    for fold in disruption_results[
        "folds"
    ]:

        auc = fold["roc_auc"]

        auc_text = (
            f"{auc:.3f}"
            if auc is not None
            else "N/A"
        )

        print(
            f"Fold {fold['fold']}: "
            f"accuracy="
            f"{fold['accuracy']:.3f}, "
            f"auc="
            f"{auc_text}, "
            f"log_loss="
            f"{fold['log_loss']:.3f}"
        )

    return {
        "basic":
            basic_results,

        "contextual":
            contextual_results,

        "farming_disruption":
            disruption_results,
    }