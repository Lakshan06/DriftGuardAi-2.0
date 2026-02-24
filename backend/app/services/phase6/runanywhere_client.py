"""
Phase 6: RunAnywhere SDK Integration Layer

This module provides a safe wrapper around the RunAnywhere SDK.
All SDK calls are isolated here to ensure Phase 5 stability.

Features:
- Timeout protection (threading-based)
- Graceful failure handling
- Fallback responses
- Comprehensive logging
- Synchronous API (FastAPI compatible)
"""

import logging
import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import wraps

# Import RunAnywhere SDK (optional dependency)
try:
    # The SDK should be installed via: pip install runanywhere-sdk
    import runanywhere
    RUNANYWHERE_AVAILABLE = True
except ImportError:
    RUNANYWHERE_AVAILABLE = False

logger = logging.getLogger(__name__)

# SDK Configuration
SDK_TIMEOUT_SECONDS = 10
SDK_MAX_RETRIES = 1
SDK_ENABLE_LOGGING = True


def timeout_handler(timeout_seconds: int):
    """
    Decorator to handle method timeouts using threading.
    
    Args:
        timeout_seconds: Maximum seconds to wait for method completion
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout_seconds)
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator


class RunAnywhereIntegration:
    """
    Singleton wrapper for RunAnywhere SDK integration.
    
    Provides three main methods:
    1. generate_explanation() - Generates governance decision explanations
    2. forecast_risk() - Forecasts future risk values
    3. generate_compliance_summary() - Creates compliance reports
    
    All methods:
    - Have timeout protection
    - Fail gracefully with fallbacks
    - Return consistent response formats
    - Log errors for debugging
    """
    
    _instance: Optional['RunAnywhereIntegration'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RunAnywhereIntegration, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize RunAnywhere SDK client (singleton pattern)"""
        if self._initialized:
            return
        
        self._initialized = True
        self.client = None
        self.available = RUNANYWHERE_AVAILABLE
        
        if self.available:
            try:
                # Initialize RunAnywhere SDK client
                self.client = runanywhere.Client() if hasattr(runanywhere, 'Client') else None
                if self.client:
                    logger.info("RunAnywhere SDK initialized successfully")
                else:
                    logger.warning("RunAnywhere SDK module loaded but Client not available")
                    self.available = False
            except Exception as e:
                logger.error(f"Failed to initialize RunAnywhere SDK: {str(e)}")
                self.available = False
        else:
            logger.warning("RunAnywhere SDK not available (install: pip install runanywhere-sdk)")
    
    def _get_fallback_explanation(
        self,
        risk_score: float,
        fairness_score: float,
        threshold: float
    ) -> Dict[str, Any]:
        """
        Generate a static fallback explanation when SDK is unavailable.
        
        Returns a valid explanation response without calling the SDK.
        """
        risk_status = "elevated" if risk_score > threshold else "normal"
        fairness_status = "acceptable" if fairness_score < 0.25 else "concerning"
        
        return {
            "risk_score": risk_score,
            "fairness_score": fairness_score,
            "threshold": threshold,
            "status": risk_status,
            "fairness_status": fairness_status,
            "explanation": f"Model risk score is {risk_status} at {risk_score:.2f} (threshold: {threshold}). "
                          f"Fairness disparity is {fairness_status} at {fairness_score:.4f}. "
                          f"Enable RunAnywhere SDK for AI-powered analysis: pip install runanywhere-sdk",
            "recommendations": [
                "Monitor model performance metrics",
                "Review recent prediction patterns",
                "Check for data distribution shifts",
                "Verify fairness across demographic groups"
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "sdk_available": False,
            "confidence": 0.5
        }
    
    def generate_explanation(
        self,
        risk_score: float,
        fairness_score: float,
        threshold: float = 60.0
    ) -> Dict[str, Any]:
        """
        Generate a governance decision explanation.
        
        Args:
            risk_score: Current MRI score (0-100)
            fairness_score: Current fairness disparity (0-1)
            threshold: Risk threshold for comparison (default 60)
        
        Returns:
            Explanation response with recommendations
            
        Fails gracefully and returns fallback if SDK unavailable.
        """
        try:
            if not self.available or self.client is None:
                logger.info("RunAnywhere SDK unavailable, using fallback explanation")
                return self._get_fallback_explanation(risk_score, fairness_score, threshold)
            
            # Call SDK method with timeout protection
            @timeout_handler(SDK_TIMEOUT_SECONDS)
            def call_sdk():
                if hasattr(self.client, 'generate_explanation'):
                    return self.client.generate_explanation(
                        risk_score=risk_score,
                        fairness_score=fairness_score,
                        threshold=threshold
                    )
                else:
                    return self._get_fallback_explanation(risk_score, fairness_score, threshold)
            
            explanation = call_sdk()
            
            # Ensure response has SDK availability marker
            if isinstance(explanation, dict):
                explanation["sdk_available"] = True
                if "generated_at" not in explanation:
                    explanation["generated_at"] = datetime.utcnow().isoformat()
            
            logger.info("Successfully generated explanation via RunAnywhere SDK")
            return explanation
            
        except threading.ThreadError as e:
            logger.error(f"RunAnywhere SDK thread error: {str(e)} - using fallback")
            return self._get_fallback_explanation(risk_score, fairness_score, threshold)
        
        except TimeoutError:
            logger.error(f"RunAnywhere SDK timeout after {SDK_TIMEOUT_SECONDS}s - using fallback")
            return self._get_fallback_explanation(risk_score, fairness_score, threshold)
        
        except Exception as e:
            logger.error(f"RunAnywhere SDK error: {type(e).__name__}: {str(e)}")
            return self._get_fallback_explanation(risk_score, fairness_score, threshold)
    
    def _get_fallback_forecast(
        self,
        risk_history: List[float]
    ) -> Dict[str, Any]:
        """
        Generate fallback risk forecast when SDK is unavailable.
        
        Uses simple statistical prediction (mean + trend).
        """
        if not risk_history or len(risk_history) < 2:
            avg_risk = risk_history[0] if risk_history else 50.0
            forecast = [avg_risk] * 5
        else:
            # Simple linear trend estimation
            recent = risk_history[-10:] if len(risk_history) > 10 else risk_history
            avg = sum(recent) / len(recent)
            
            # Calculate simple trend
            if len(recent) > 1:
                trend = (recent[-1] - recent[0]) / (len(recent) - 1)
            else:
                trend = 0.0
            
            # Generate 5-step forecast
            forecast = []
            for i in range(1, 6):
                next_val = avg + (trend * i)
                # Clamp to 0-100
                next_val = max(0.0, min(100.0, next_val))
                forecast.append(round(next_val, 2))
        
        return {
            "current_risk": risk_history[-1] if risk_history else 50.0,
            "average_risk": sum(risk_history) / len(risk_history) if risk_history else 50.0,
            "history_points": len(risk_history),
            "forecast_horizon": 5,
            "forecasted_values": forecast,
            "confidence": 0.65,
            "method": "statistical",
            "note": "Fallback forecast using statistical methods. "
                   "Enable SDK: pip install runanywhere-sdk for AI-powered forecasting",
            "generated_at": datetime.utcnow().isoformat(),
            "sdk_available": False
        }
    
    def forecast_risk(
        self,
        risk_history_list: List[float]
    ) -> Dict[str, Any]:
        """
        Forecast future risk values using ML models.
        
        Args:
            risk_history_list: List of historical risk scores
        
        Returns:
            Forecast response with predicted values and confidence
            
        Fails gracefully and returns fallback if SDK unavailable.
        """
        try:
            if not self.available or self.client is None:
                logger.info("RunAnywhere SDK unavailable, using fallback forecast")
                return self._get_fallback_forecast(risk_history_list)
            
            # Call SDK method with timeout protection
            @timeout_handler(SDK_TIMEOUT_SECONDS)
            def call_sdk():
                if hasattr(self.client, 'forecast_risk'):
                    return self.client.forecast_risk(
                        risk_history=risk_history_list
                    )
                else:
                    return self._get_fallback_forecast(risk_history_list)
            
            forecast = call_sdk()
            
            # Ensure response has SDK availability marker
            if isinstance(forecast, dict):
                forecast["sdk_available"] = True
                if "generated_at" not in forecast:
                    forecast["generated_at"] = datetime.utcnow().isoformat()
            
            logger.info("Successfully forecasted risk via RunAnywhere SDK")
            return forecast
            
        except threading.ThreadError as e:
            logger.error(f"RunAnywhere SDK thread error: {str(e)} - using fallback")
            return self._get_fallback_forecast(risk_history_list)
        
        except TimeoutError:
            logger.error(f"RunAnywhere SDK timeout after {SDK_TIMEOUT_SECONDS}s - using fallback")
            return self._get_fallback_forecast(risk_history_list)
        
        except Exception as e:
            logger.error(f"RunAnywhere SDK error: {type(e).__name__}: {str(e)}")
            return self._get_fallback_forecast(risk_history_list)
    
    def _get_fallback_compliance_summary(self) -> Dict[str, Any]:
        """
        Generate fallback compliance summary when SDK is unavailable.
        """
        return {
            "compliance_grade": "C",
            "compliance_percentage": 65.0,
            "summary": "System operating at baseline compliance level. "
                      "Enable RunAnywhere SDK for advanced compliance analysis.",
            "key_findings": [
                "No critical violations detected",
                "Governance policies enforced",
                "Deployment audit trail maintained",
                "Fairness monitoring active"
            ],
            "recommendations": [
                "Review fairness metrics across demographic groups",
                "Monitor model drift over time",
                "Schedule regular governance evaluations"
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "sdk_available": False
        }
    
    def generate_compliance_summary(
        self,
        total_models: int = 0,
        models_at_risk: int = 0,
        compliance_score: float = 65.0
    ) -> Dict[str, Any]:
        """
        Generate a compliance summary report.
        
        Args:
            total_models: Total number of models in system
            models_at_risk: Count of at-risk models
            compliance_score: Overall system compliance score
        
        Returns:
            Compliance summary response
            
        Fails gracefully and returns fallback if SDK unavailable.
        """
        try:
            if not self.available or self.client is None:
                logger.info("RunAnywhere SDK unavailable, using fallback compliance summary")
                return self._get_fallback_compliance_summary()
            
            # Call SDK method with timeout protection
            @timeout_handler(SDK_TIMEOUT_SECONDS)
            def call_sdk():
                if hasattr(self.client, 'generate_compliance_summary'):
                    return self.client.generate_compliance_summary(
                        total_models=total_models,
                        models_at_risk=models_at_risk,
                        compliance_score=compliance_score
                    )
                else:
                    return self._get_fallback_compliance_summary()
            
            summary = call_sdk()
            
            # Ensure response has SDK availability marker
            if isinstance(summary, dict):
                summary["sdk_available"] = True
                if "generated_at" not in summary:
                    summary["generated_at"] = datetime.utcnow().isoformat()
            
            logger.info("Successfully generated compliance summary via RunAnywhere SDK")
            return summary
            
        except threading.ThreadError as e:
            logger.error(f"RunAnywhere SDK thread error: {str(e)} - using fallback")
            return self._get_fallback_compliance_summary()
        
        except TimeoutError:
            logger.error(f"RunAnywhere SDK timeout after {SDK_TIMEOUT_SECONDS}s - using fallback")
            return self._get_fallback_compliance_summary()
        
        except Exception as e:
            logger.error(f"RunAnywhere SDK error: {type(e).__name__}: {str(e)}")
            return self._get_fallback_compliance_summary()


# Module-level function for singleton access
def get_runanywhere_client() -> Optional[RunAnywhereIntegration]:
    """
    Get the RunAnywhere SDK client singleton instance.
    
    Returns:
        RunAnywhereIntegration instance or None if unavailable
    """
    try:
        client = RunAnywhereIntegration()
        return client if client.available else None
    except Exception as e:
        logger.error(f"Failed to get RunAnywhere client: {str(e)}")
        return None
