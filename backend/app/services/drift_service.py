import numpy as np
from scipy import stats
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from app.models.prediction_log import PredictionLog
from app.models.drift_metric import DriftMetric
from app.models.model_registry import ModelRegistry
from app.core.config import settings


def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Population Stability Index (PSI)
    
    PSI = sum((actual_% - expected_%) * ln(actual_% / expected_%))
    
    Interpretation:
    - PSI < 0.1: No significant change
    - 0.1 <= PSI < 0.25: Moderate change
    - PSI >= 0.25: Significant change
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    
    # Create bins based on expected distribution
    min_val = min(expected.min(), actual.min())
    max_val = max(expected.max(), actual.max())
    breakpoints = np.linspace(min_val, max_val, bins + 1)
    
    # Calculate histograms
    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)
    
    # Convert to percentages (add small value to avoid division by zero)
    expected_percents = (expected_counts + 1e-6) / (expected_counts.sum() + bins * 1e-6)
    actual_percents = (actual_counts + 1e-6) / (actual_counts.sum() + bins * 1e-6)
    
    # Calculate PSI
    psi_values = (actual_percents - expected_percents) * np.log(actual_percents / expected_percents)
    psi = np.sum(psi_values)
    
    return float(psi)


def calculate_ks_statistic(expected: np.ndarray, actual: np.ndarray) -> float:
    """
    Calculate Kolmogorov-Smirnov test statistic
    
    Returns KS statistic (0-1):
    - Values close to 0 indicate similar distributions
    - Values close to 1 indicate very different distributions
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    
    ks_statistic, _ = stats.ks_2samp(expected, actual)
    return float(ks_statistic)


def get_baseline_data(db: Session, model_id: int, feature_name: str) -> np.ndarray:
    """
    Get baseline data for a feature from model's schema_definition
    or from early prediction logs (first 100 records)
    """
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    
    if not model:
        return np.array([])
    
    # Get early prediction logs as baseline
    baseline_logs = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id
    ).order_by(PredictionLog.timestamp.asc()).limit(100).all()
    
    if not baseline_logs:
        return np.array([])
    
    # Extract feature values from baseline
    baseline_values = []
    for log in baseline_logs:
        if feature_name in log.input_features:
            try:
                # Try to convert to float (works for numeric features)
                baseline_values.append(float(log.input_features[feature_name]))
            except (ValueError, TypeError):
                # Skip categorical features - they can't be used for PSI/KS
                pass
        elif feature_name == "prediction":
            baseline_values.append(float(log.prediction))
    
    return np.array(baseline_values)


def get_recent_data(db: Session, model_id: int, feature_name: str, window_size: int = None) -> np.ndarray:
    """
    Get recent production data for a feature using sliding window
    """
    if window_size is None:
        window_size = settings.DRIFT_WINDOW_SIZE
    
    recent_logs = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id
    ).order_by(PredictionLog.timestamp.desc()).limit(window_size).all()
    
    if not recent_logs:
        return np.array([])
    
    recent_values = []
    for log in recent_logs:
        if feature_name in log.input_features:
            try:
                # Try to convert to float (works for numeric features)
                recent_values.append(float(log.input_features[feature_name]))
            except (ValueError, TypeError):
                # Skip categorical features - they can't be used for PSI/KS
                pass
        elif feature_name == "prediction":
            recent_values.append(float(log.prediction))
    
    return np.array(recent_values)


def calculate_drift_for_model(db: Session, model_id: int) -> List[DriftMetric]:
    """
    Calculate drift metrics for all features of a model
    Returns list of DriftMetric objects that were created
    """
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    
    if not model:
        return []
    
    # Identify features to monitor
    features_to_monitor = []
    
    # Get features from prediction logs
    sample_log = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id
    ).first()
    
    if sample_log and sample_log.input_features:
        features_to_monitor = list(sample_log.input_features.keys())
    
    # Always monitor prediction distribution
    features_to_monitor.append("prediction")
    
    drift_metrics = []
    
    for feature_name in features_to_monitor:
        baseline = get_baseline_data(db, model_id, feature_name)
        recent = get_recent_data(db, model_id, feature_name)
        
        if len(baseline) < 10 or len(recent) < 10:
            continue
        
        # Calculate PSI and KS statistic
        psi_value = calculate_psi(baseline, recent)
        ks_statistic = calculate_ks_statistic(baseline, recent)
        
        # Determine drift flag
        drift_flag = (psi_value >= settings.PSI_THRESHOLD) or (ks_statistic >= settings.KS_THRESHOLD)
        
        # Create drift metric record
        drift_metric = DriftMetric(
            model_id=model_id,
            feature_name=feature_name,
            psi_value=psi_value,
            ks_statistic=ks_statistic,
            drift_flag=drift_flag,
            timestamp=datetime.utcnow()
        )
        
        db.add(drift_metric)
        drift_metrics.append(drift_metric)
    
    db.commit()
    
    return drift_metrics


def get_drift_metrics_for_model(db: Session, model_id: int, limit: int = 100) -> List[DriftMetric]:
    """
    Get recent drift metrics for a model
    """
    return db.query(DriftMetric).filter(
        DriftMetric.model_id == model_id
    ).order_by(DriftMetric.timestamp.desc()).limit(limit).all()
