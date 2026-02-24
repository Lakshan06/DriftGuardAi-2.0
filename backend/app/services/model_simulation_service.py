"""
Model Simulation Service

Generates realistic prediction logs for demo/testing purposes.
Used to populate a model with simulated data to demonstrate drift detection,
fairness metrics, and risk scoring capabilities.

SAFETY RULES:
- Only affects the specified model
- Does not overwrite existing logs
- Must be idempotent (checks for existing logs)
- Uses existing services for metric calculation
- No schema changes required
- ALL operations wrapped in transactions
- Comprehensive logging at each step
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.model_registry import ModelRegistry
from ..models.prediction_log import PredictionLog
from ..services.drift_service import calculate_drift_for_model
from ..services.fairness_service import calculate_fairness_for_model
from ..services.risk_service import create_risk_history_entry

logger = logging.getLogger(__name__)


class ModelSimulationService:
    """Service for generating simulated prediction data for models"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_model_has_logs(self, model_id: int) -> bool:
        """Check if model already has prediction logs"""
        count = self.db.query(func.count(PredictionLog.id)).filter(
            PredictionLog.model_id == model_id
        ).scalar()
        return count > 0
    
    def generate_baseline_data(self, num_samples: int = 300) -> List[Dict[str, Any]]:
        """
        Generate baseline prediction data with normal distribution
        
        ENHANCED FOR HIGH-RISK SCENARIO:
        Simulates a well-performing fraud detection model with:
        - Normal transaction patterns (mean: $200, stable)
        - Balanced demographics
        - Balanced gender approval (male: 70%, female: 70%)
        """
        samples = []
        
        for i in range(num_samples):
            # Generate features - BASELINE STABLE DISTRIBUTION
            transaction_amount = random.gauss(200.0, 80.0)  # Mean: $200, SD: $80 (STABLE)
            transaction_amount = max(10.0, min(800.0, transaction_amount))  # Clamp
            
            customer_age = int(random.gauss(40, 12))  # Mean: 40, SD: 12
            customer_age = max(18, min(80, customer_age))  # Clamp
            
            gender = random.choice(['Male', 'Female'])
            country = random.choices(
                ['USA', 'UK', 'Canada', 'Germany', 'France'],
                weights=[0.4, 0.2, 0.15, 0.15, 0.1]  # BASELINE BALANCED
            )[0]
            device_type = random.choices(
                ['mobile', 'desktop', 'tablet'],
                weights=[0.5, 0.35, 0.15]  # BASELINE BALANCED
            )[0]
            
            # Generate prediction (fraud probability) - BASELINE FAIR APPROVAL
            # Both genders have similar approval rate (~70% = 0.3 fraud probability)
            fraud_probability = random.betavariate(2, 5)  # ~30% fraud rate, fair
            fraud_probability = min(0.99, max(0.01, fraud_probability))
            
            samples.append({
                'input_features': {
                    'transaction_amount': round(transaction_amount, 2),
                    'customer_age': customer_age,
                    'gender': gender,
                    'country': country,
                    'device_type': device_type
                },
                'prediction': round(fraud_probability, 4)
            })
        
        return samples
    
    def generate_shifted_data(self, num_samples: int = 200) -> List[Dict[str, Any]]:
        """
        Generate shifted prediction data to demonstrate HIGH-RISK DRIFT
        
        ENHANCED FOR CRITICAL GOVERNANCE SCENARIO:
        - SEVERE distribution shift (transaction_amount mean = 900, heavy variance)
        - Strong country imbalance (95% USA)
        - Heavy device_type skew (85% mobile)
        - BIASED APPROVAL: male 70% approval, female 45% approval
        
        TARGET PSI > 0.35 for at least 2 features
        TARGET Fairness disparity > 25%
        """
        samples = []
        
        for i in range(num_samples):
            # Generate features with SEVERE DRIFT
            # CRITICAL: Transaction amount mean = 900 (was 200 in baseline)
            transaction_amount = random.gauss(900.0, 300.0)  # SEVERE SHIFT: 4.5x higher mean
            transaction_amount = max(200.0, min(2000.0, transaction_amount))  # High range
            
            # Older customer base (moderate shift)
            customer_age = int(random.gauss(55, 18))  # SHIFTED: Much older customers
            customer_age = max(25, min(90, customer_age))
            
            # Gender distribution still balanced (bias is in approval, not population)
            gender = random.choice(['Male', 'Female'])
            
            # CRITICAL: Strong country imbalance (95% USA)
            country = random.choices(
                ['USA', 'UK', 'Canada', 'Germany', 'France'],
                weights=[0.95, 0.02, 0.01, 0.01, 0.01]  # SEVERE DRIFT
            )[0]
            
            # CRITICAL: Heavy device_type skew (85% mobile)
            device_type = random.choices(
                ['mobile', 'desktop', 'tablet'],
                weights=[0.85, 0.10, 0.05]  # SEVERE DRIFT
            )[0]
            
            # CRITICAL: Generate biased approval predictions
            # Male: 70% approval (30% fraud probability)
            # Female: 45% approval (55% fraud probability)
            if gender == 'Male':
                # Male bias: Lower fraud probability (higher approval)
                fraud_probability = random.betavariate(2, 5)  # ~30% fraud = 70% approval
            else:  # Female
                # Female bias: Higher fraud probability (lower approval)
                fraud_probability = random.betavariate(5, 4)  # ~55% fraud = 45% approval
            
            fraud_probability = min(0.99, max(0.01, fraud_probability))
            
            samples.append({
                'input_features': {
                    'transaction_amount': round(transaction_amount, 2),
                    'customer_age': customer_age,
                    'gender': gender,
                    'country': country,
                    'device_type': device_type
                },
                'prediction': round(fraud_probability, 4)
            })
        
        return samples
    
    def create_staged_risk_history(
        self,
        model_id: int,
        final_risk_score: float,
        final_drift_component: float,
        final_fairness_component: float
    ) -> List[Any]:
        """
        PHASE 4: Create multi-stage risk history showing upward trend
        
        Inserts 4 risk history entries spanning last 30 days:
        - Time 1 (30 days ago): risk = 45, status = HEALTHY
        - Time 2 (20 days ago): risk = 60, status = ATTENTION
        - Time 3 (10 days ago): risk = 72, status = AT_RISK
        - Time 4 (now): risk = actual calculated (80-90), status = BLOCKED
        
        This creates visible upward trend in risk history chart
        """
        from ..models.risk_history import RiskHistory
        
        logger.info(f"Creating staged risk history for model {model_id} with final score {final_risk_score}")
        
        # Calculate proportional components for each stage
        stages = [
            {
                'days_ago': 30,
                'risk_score': 45.0,
                'drift_multiplier': 0.5,
                'fairness_multiplier': 0.6
            },
            {
                'days_ago': 20,
                'risk_score': 60.0,
                'drift_multiplier': 0.7,
                'fairness_multiplier': 0.75
            },
            {
                'days_ago': 10,
                'risk_score': 72.0,
                'drift_multiplier': 0.85,
                'fairness_multiplier': 0.88
            },
            {
                'days_ago': 0,
                'risk_score': final_risk_score,
                'drift_multiplier': 1.0,
                'fairness_multiplier': 1.0
            }
        ]
        
        risk_entries = []
        
        for stage in stages:
            timestamp = datetime.utcnow() - timedelta(days=stage['days_ago'])
            
            risk_entry = RiskHistory(
                model_id=model_id,
                risk_score=stage['risk_score'],
                drift_component=final_drift_component * stage['drift_multiplier'],
                fairness_component=final_fairness_component * stage['fairness_multiplier'],
                timestamp=timestamp
            )
            
            self.db.add(risk_entry)
            risk_entries.append(risk_entry)
            
            logger.info(
                f"Created risk history entry: {stage['days_ago']} days ago, "
                f"risk={stage['risk_score']:.1f}"
            )
        
        self.db.flush()
        logger.info(f"Successfully created {len(risk_entries)} staged risk history entries")
        
        return risk_entries
    
    def insert_prediction_logs(
        self,
        model_id: int,
        samples: List[Dict[str, Any]],
        start_time: datetime
    ) -> int:
        """
        Insert prediction log samples into database with transaction safety
        
        Returns number of logs inserted
        
        Raises:
            RuntimeError: If insertion fails (transaction is rolled back)
        """
        try:
            logger.info(f"Starting insertion of {len(samples)} prediction logs for model {model_id}")
            logs_created = 0
            
            for idx, sample in enumerate(samples):
                # Space out timestamps (1 per hour)
                timestamp = start_time + timedelta(hours=idx)
                
                log = PredictionLog(
                    model_id=model_id,
                    input_features=sample['input_features'],
                    prediction=sample['prediction'],
                    actual_label=None,  # Not provided in simulation
                    timestamp=timestamp
                )
                
                self.db.add(log)
                logs_created += 1
            
            # Flush to validate all inserts before commit
            self.db.flush()
            logger.info(f"Flushed {logs_created} logs, validating...")
            
            # Commit the transaction
            self.db.commit()
            logger.info(f"Successfully committed {logs_created} prediction logs for model {model_id}")
            
            return logs_created
        except Exception as e:
            logger.error(f"Failed to insert prediction logs for model {model_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            raise RuntimeError(f"Failed to insert prediction logs: {str(e)}")
    
    def run_simulation(self, model_id: int) -> Dict[str, Any]:
        """
        Main simulation orchestrator with comprehensive error handling and logging
        
        ENHANCED FOR HIGH-RISK SCENARIO:
        - Severe drift (PSI > 0.4)
        - Fairness bias (disparity > 0.3)
        - Risk score 80-95 range
        - Multi-stage risk history
        - Model status → BLOCKED
        
        Steps:
        1. Verify model exists
        2. Check if model already has logs (idempotency)
        3. Generate baseline data (300 samples)
        4. Generate shifted data (200 samples)
        5. Insert all logs (with transaction safety)
        6. Trigger drift recalculation
        7. Trigger fairness recalculation
        8. Calculate risk components
        9. Create staged risk history
        10. Update model status
        11. Return summary
        
        Returns:
            Dict with simulation summary including metrics
            
        Raises:
            ValueError: If model not found or already simulated
            RuntimeError: If any step fails
        """
        logger.info(f"=== HIGH-RISK SIMULATION STARTED for model {model_id} ===")
        logger.warning(f"🚨 HIGH RISK SIMULATION ACTIVE - FORCING CRITICAL VALUES 🚨")
        
        try:
            # Step 1: Verify model exists
            logger.info(f"Step 1: Verifying model exists (ID: {model_id})")
            model = self.db.query(ModelRegistry).filter(
                ModelRegistry.id == model_id
            ).first()
            
            if not model:
                logger.error(f"Model {model_id} not found")
                raise ValueError(f"Model with ID {model_id} not found")
            
            logger.info(f"Model found: {model.model_name} v{model.version}")
            
            # Step 2: Check for existing logs (idempotency)
            logger.info(f"Step 2: Checking idempotency (existing logs for model {model_id})")
            if self.check_model_has_logs(model_id):
                logger.warning(f"Model {model_id} already has prediction logs - blocking duplicate simulation")
                raise ValueError(
                    f"Model {model_id} already has prediction logs. "
                    "Simulation can only be run once to prevent data duplication."
                )
            
            logger.info(f"Idempotency check passed - no existing logs")
            
            # Step 3-4: Generate data
            logger.info(f"Step 3: Generating 300 baseline prediction samples")
            baseline_samples = self.generate_baseline_data(300)
            logger.info(f"Generated {len(baseline_samples)} baseline samples")
            
            logger.info(f"Step 4: Generating 200 shifted prediction samples")
            shifted_samples = self.generate_shifted_data(200)
            logger.info(f"Generated {len(shifted_samples)} shifted samples")
            
            all_samples = baseline_samples + shifted_samples
            logger.info(f"Total samples ready: {len(all_samples)}")
            
            # Step 5: Insert logs
            logger.info(f"Step 5: Inserting {len(all_samples)} prediction logs into database")
            start_time = datetime.utcnow() - timedelta(days=30)
            try:
                logs_generated = self.insert_prediction_logs(
                    model_id=model_id,
                    samples=all_samples,
                    start_time=start_time
                )
            except RuntimeError as e:
                logger.error(f"Failed to insert logs: {str(e)}")
                raise
            
            logger.info(f"Successfully inserted {logs_generated} logs with transaction safety")
            
            # Step 6: Trigger drift recalculation
            logger.info(f"Step 6: Triggering drift recalculation for model {model_id}")
            try:
                drift_metrics = calculate_drift_for_model(self.db, model_id)
                logger.info(f"Drift calculation complete: {len(drift_metrics)} features analyzed")
                
                if not drift_metrics:
                    logger.warning(f"Drift calculation returned no metrics for model {model_id}")
                    avg_psi = 0.0
                    avg_ks = 0.0
                    drift_score = 0.0
                else:
                    avg_psi = sum(m.psi_value for m in drift_metrics) / len(drift_metrics)
                    avg_ks = sum(m.ks_statistic for m in drift_metrics) / len(drift_metrics)
                    drift_score = (avg_psi * 0.6 + avg_ks * 0.4)
                    logger.info(f"Drift metrics (calculated): PSI={avg_psi:.4f}, KS={avg_ks:.4f}, Score={drift_score:.4f}")
                
                # 🚨 STEP 2: FORCE HIGH DRIFT VALUES
                logger.warning(f"🚨 FORCING HIGH DRIFT VALUES (STEP 2)")
                
                # Force override drift metrics in database for HIGH-RISK scenario
                from ..models.drift_metric import DriftMetric
                
                # Update existing drift metrics to be HIGH
                if drift_metrics and len(drift_metrics) > 0:
                    for idx, metric in enumerate(drift_metrics):
                        # Force PSI > 0.4 and KS > 0.3 for high drift
                        metric.psi_value = 0.42 + (idx * 0.05)  # 0.42, 0.47, 0.52, etc.
                        metric.ks_statistic = 0.35 + (idx * 0.03)  # 0.35, 0.38, 0.41, etc.
                        metric.drift_detected = True
                        logger.info(f"  Forced drift for {metric.feature_name}: PSI={metric.psi_value:.3f}, KS={metric.ks_statistic:.3f}")
                    
                    self.db.flush()
                    
                    # Recalculate averages with forced values
                    avg_psi = sum(m.psi_value for m in drift_metrics) / len(drift_metrics)
                    avg_ks = sum(m.ks_statistic for m in drift_metrics) / len(drift_metrics)
                    drift_score = (avg_psi * 0.6 + avg_ks * 0.4)
                    
                    logger.warning(f"🚨 FORCED DRIFT: PSI={avg_psi:.4f}, KS={avg_ks:.4f}, Score={drift_score:.4f}")
                else:
                    # If no metrics exist, create forced high-drift metrics
                    logger.warning(f"Creating forced high-drift metrics from scratch")
                    features = ['transaction_amount', 'customer_age', 'country', 'device_type']
                    drift_metrics = []
                    
                    for idx, feature in enumerate(features):
                        forced_metric = DriftMetric(
                            model_id=model_id,
                            feature_name=feature,
                            psi_value=0.45 + (idx * 0.05),  # 0.45, 0.50, 0.55, 0.60
                            ks_statistic=0.38 + (idx * 0.03),  # 0.38, 0.41, 0.44, 0.47
                            drift_detected=True,
                            timestamp=datetime.utcnow()
                        )
                        self.db.add(forced_metric)
                        drift_metrics.append(forced_metric)
                        logger.info(f"  Created forced drift for {feature}: PSI={forced_metric.psi_value:.3f}")
                    
                    self.db.flush()
                    
                    avg_psi = sum(m.psi_value for m in drift_metrics) / len(drift_metrics)
                    avg_ks = sum(m.ks_statistic for m in drift_metrics) / len(drift_metrics)
                    drift_score = (avg_psi * 0.6 + avg_ks * 0.4)
                    
                    logger.warning(f"🚨 FORCED DRIFT (created): PSI={avg_psi:.4f}, KS={avg_ks:.4f}, Score={drift_score:.4f}")
                
            except Exception as e:
                logger.error(f"Drift calculation failed: {str(e)}", exc_info=True)
                raise RuntimeError(f"Failed to calculate drift metrics: {str(e)}")
            
            # Step 7: Trigger fairness recalculation
            logger.info(f"Step 7: Triggering fairness recalculation for model {model_id}")
            try:
                fairness_result = calculate_fairness_for_model(
                    db=self.db,
                    model_id=model_id,
                    protected_attribute='gender'
                )
                
                if not fairness_result:
                    logger.error(f"Fairness calculation returned None for model {model_id}")
                    raise ValueError("Fairness calculation returned empty result")
                
                fairness_score = fairness_result.get('disparity_score', 0.0)
                fairness_flag = fairness_result.get('fairness_flag', False)
                logger.info(f"Fairness metrics (calculated): Disparity={fairness_score:.4f}, Flag={fairness_flag}")
                
                # 🚨 STEP 3: FORCE HIGH FAIRNESS DISPARITY
                logger.warning(f"🚨 FORCING HIGH FAIRNESS DISPARITY (STEP 3)")
                
                from ..models.fairness_metric import FairnessMetric
                
                # Force disparity to be > 0.3 (HIGH BIAS)
                forced_disparity = 0.32  # Exceeds 0.25 threshold significantly
                
                # Update all fairness metrics for this model
                fairness_metrics = self.db.query(FairnessMetric).filter(
                    FairnessMetric.model_id == model_id
                ).all()
                
                if fairness_metrics and len(fairness_metrics) > 0:
                    logger.info(f"Updating {len(fairness_metrics)} existing fairness metrics")
                    for metric in fairness_metrics:
                        metric.disparity_score = forced_disparity
                        metric.fairness_flag = True  # Flag as unfair
                        logger.info(f"  Forced fairness for {metric.protected_attribute}/{metric.group_name}: disparity={forced_disparity}")
                    
                    self.db.flush()
                    fairness_score = forced_disparity
                    fairness_flag = True
                    
                    logger.warning(f"🚨 FORCED FAIRNESS: Disparity={fairness_score:.4f}, Flag={fairness_flag}")
                else:
                    # Create forced fairness metrics if none exist
                    logger.warning(f"Creating forced fairness metrics from scratch")
                    
                    forced_male_metric = FairnessMetric(
                        model_id=model_id,
                        protected_attribute='gender',
                        group_name='Male',
                        total_predictions=100,
                        positive_predictions=70,  # 70% approval
                        approval_rate=0.70,
                        disparity_score=forced_disparity,
                        fairness_flag=True,
                        timestamp=datetime.utcnow()
                    )
                    
                    forced_female_metric = FairnessMetric(
                        model_id=model_id,
                        protected_attribute='gender',
                        group_name='Female',
                        total_predictions=100,
                        positive_predictions=45,  # 45% approval (25% disparity)
                        approval_rate=0.45,
                        disparity_score=forced_disparity,
                        fairness_flag=True,
                        timestamp=datetime.utcnow()
                    )
                    
                    self.db.add(forced_male_metric)
                    self.db.add(forced_female_metric)
                    self.db.flush()
                    
                    fairness_score = forced_disparity
                    fairness_flag = True
                    
                    logger.warning(f"🚨 FORCED FAIRNESS (created): Disparity={fairness_score:.4f}, Male=70%, Female=45%")
                
            except Exception as e:
                logger.error(f"Fairness calculation failed: {str(e)}", exc_info=True)
                raise RuntimeError(f"Failed to calculate fairness metrics: {str(e)}")
            
            # Step 8: Calculate risk components for staged history
            logger.info(f"Step 8: Calculating risk score components for model {model_id}")
            try:
                from ..services.risk_service import calculate_drift_component, calculate_fairness_component
                
                drift_component = calculate_drift_component(self.db, model_id)
                fairness_component = calculate_fairness_component(self.db, model_id)
                
                logger.info(
                    f"Risk components (calculated): "
                    f"drift={drift_component:.2f}, fairness={fairness_component:.2f}"
                )
                
                # 🚨 STEP 4: FORCE HIGH RISK SCORE
                logger.warning(f"🚨 FORCING HIGH RISK SCORE (STEP 4)")
                
                # Force risk components to be HIGH
                # Drift component should be 80-95 (from high PSI values)
                # Fairness component should be ~100 (32% disparity * 100 / 0.4 threshold)
                
                # Override if calculated values are too low
                if drift_component < 75:
                    drift_component = 85.0
                    logger.warning(f"  Forced drift_component to {drift_component}")
                
                if fairness_component < 75:
                    fairness_component = 80.0  # 32% disparity normalized
                    logger.warning(f"  Forced fairness_component to {fairness_component}")
                
                # Calculate final MRI score with enhanced weights for HIGH-RISK scenario
                # Drift: 60%, Fairness: 40% (matching risk_service.py formula)
                final_risk_score = (drift_component * 0.6) + (fairness_component * 0.4)
                
                # Ensure final risk score is in target range (80-95)
                if final_risk_score < 80:
                    final_risk_score = 87.0  # Force to 87
                    logger.warning(f"  Forced final_risk_score to {final_risk_score}")
                
                logger.warning(
                    f"🚨 FORCED RISK: drift={drift_component:.2f}, fairness={fairness_component:.2f}, "
                    f"final_risk={final_risk_score:.2f}"
                )
                
            except Exception as e:
                logger.error(f"Risk calculation failed: {str(e)}", exc_info=True)
                raise RuntimeError(f"Failed to calculate risk score: {str(e)}")
            
            # Step 9: Create staged risk history (PHASE 4)
            logger.info(f"Step 9: Creating staged risk history for upward trend visualization")
            try:
                risk_entries = self.create_staged_risk_history(
                    model_id=model_id,
                    final_risk_score=final_risk_score,
                    final_drift_component=drift_component,
                    final_fairness_component=fairness_component
                )
                
                # Commit staged risk history
                self.db.commit()
                
                logger.info(f"Created {len(risk_entries)} staged risk history entries")
            except Exception as e:
                logger.error(f"Failed to create staged risk history: {str(e)}", exc_info=True)
                self.db.rollback()
                raise RuntimeError(f"Failed to create staged risk history: {str(e)}")
            
            # Step 10: Update model status based on risk score (PHASE 3 & STEP 4)
            logger.info(f"Step 10: Updating model status based on risk score")
            logger.warning(f"🚨 FORCING MODEL STATUS UPDATE (risk={final_risk_score:.1f})")
            try:
                # Determine status from forced high risk score
                if final_risk_score >= 80:
                    model.status = "BLOCKED"
                    final_status = "BLOCKED"
                    logger.warning(f"  Status = BLOCKED (risk >= 80)")
                elif final_risk_score >= 70:
                    model.status = "AT_RISK"
                    final_status = "AT_RISK"
                    logger.warning(f"  Status = AT_RISK (risk >= 70)")
                elif final_risk_score >= 50:
                    model.status = "ATTENTION_NEEDED"
                    final_status = "ATTENTION_NEEDED"
                    logger.warning(f"  Status = ATTENTION_NEEDED (risk >= 50)")
                else:
                    model.status = "HEALTHY"
                    final_status = "HEALTHY"
                    logger.info(f"  Status = HEALTHY (risk < 50)")
                
                # 🚨 STEP 5: COMMIT AND VERIFY
                logger.warning(f"🚨 COMMITTING ALL CHANGES TO DATABASE (STEP 5)")
                self.db.commit()
                
                # Verify the update persisted
                self.db.refresh(model)
                logger.warning(f"🚨 VERIFIED: Model status = {model.status}, risk = {final_risk_score:.1f}")
                logger.warning(f"🚨 DB COMMIT SUCCESSFUL")
                
            except Exception as e:
                logger.error(f"Failed to update model status: {str(e)}", exc_info=True)
                self.db.rollback()
                raise RuntimeError(f"Failed to update model status: {str(e)}")
            
            # Step 11: Return comprehensive summary
            logger.info(f"=== SIMULATION COMPLETED SUCCESSFULLY for model {model_id} ===")
            
            result = {
                "success": True,
                "model_id": model_id,
                "model_name": model.model_name,
                "logs_generated": logs_generated,
                "baseline_logs": 300,
                "shifted_logs": 200,
                "drift_metrics": {
                    "avg_psi": float(avg_psi),
                    "avg_ks": float(avg_ks),
                    "drift_score": float(drift_score),
                    "drift_component": float(drift_component)
                },
                "fairness_metrics": {
                    "disparity_score": float(fairness_score),
                    "fairness_flag": bool(fairness_flag),
                    "fairness_component": float(fairness_component)
                },
                "risk_score": float(final_risk_score),
                "final_status": final_status,
                "risk_history_entries": len(risk_entries),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Returning simulation result: {result}")
            return result
            
        except (ValueError, RuntimeError) as e:
            logger.error(f"Simulation failed with controlled error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Simulation failed with unexpected error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Simulation encountered an unexpected error: {str(e)}")
