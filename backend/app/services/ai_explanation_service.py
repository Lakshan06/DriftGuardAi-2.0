"""
Enhanced AI Explanation Service with RunAnywhere SDK integration.

This service provides AI-powered explanations for governance decisions.
Features:
- RunAnywhere SDK for real AI explanations (PRIMARY)
- Intelligent fallback explanations (FALLBACK)
- Optional Claude/OpenAI support (OPTIONAL SECONDARY)
- Context-aware analysis
- Caching for performance
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.cache import get_cache

logger = logging.getLogger(__name__)

# Try to import LLM libraries (optional)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIExplanationService:
    """
    Service for generating AI-powered governance explanations.
    
    Priority order:
    1. RunAnywhere SDK (PRIMARY) - Built-in AI intelligence
    2. Claude/OpenAI APIs (SECONDARY) - Premium LLMs if configured
    3. Intelligent templates (FALLBACK) - Always works, no external deps
    """
    
    CACHE_TTL = 3600  # Cache explanations for 1 hour
    
    @staticmethod
    def generate_governance_explanation(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool = False,
        policy_threshold: float = 60.0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI explanation for governance decision.
        
        Priority:
        1. RunAnywhere SDK (if available)
        2. Claude/OpenAI (if configured)
        3. Intelligent template (always works)
        
        Args:
            model_name: Name of the model
            risk_score: Current risk score (0-100)
            fairness_score: Current fairness disparity (0-1)
            drift_detected: Whether drift was detected
            policy_threshold: Policy risk threshold
            use_cache: Whether to use cached explanations
            
        Returns:
            Explanation dictionary with reasoning and recommendations
        """
        try:
            # Check cache first
            if use_cache:
                cache_key = f"ai_explanation:{model_name}:{risk_score:.2f}:{fairness_score:.4f}"
                cached = get_cache().get(cache_key)
                if cached:
                    logger.info(f"Using cached explanation for {model_name}")
                    cached["from_cache"] = True
                    return cached
            
            # TRY RUNANYWHERE SDK (PRIMARY)
            try:
                from app.services.phase6 import get_runanywhere_client
                runanywhere_client = get_runanywhere_client()
                if runanywhere_client:
                    result = runanywhere_client.generate_explanation(
                        risk_score=risk_score,
                        fairness_score=fairness_score,
                        threshold=policy_threshold
                    )
                    if result and isinstance(result, dict):
                        # Enhance with additional metadata
                        result["ai_source"] = "RunAnywhere SDK"
                        result["is_real_ai"] = True
                        result["model_name"] = model_name
                        if "generated_at" not in result:
                            result["generated_at"] = datetime.utcnow().isoformat()
                        if use_cache:
                            get_cache().set(
                                f"ai_explanation:{model_name}:{risk_score:.2f}:{fairness_score:.4f}",
                                result,
                                AIExplanationService.CACHE_TTL
                            )
                        logger.info(f"Generated explanation via RunAnywhere SDK for {model_name}")
                        return result
            except Exception as e:
                logger.debug(f"RunAnywhere SDK not available or error: {str(e)}")
            
            # TRY CLAUDE (SECONDARY)
            if ANTHROPIC_AVAILABLE:
                result = AIExplanationService._generate_with_claude(
                    model_name, risk_score, fairness_score, drift_detected, policy_threshold
                )
                if result:
                    result["ai_source"] = "Claude (Anthropic)"
                    result["is_real_ai"] = True
                    if use_cache:
                        get_cache().set(
                            f"ai_explanation:{model_name}:{risk_score:.2f}:{fairness_score:.4f}",
                            result,
                            AIExplanationService.CACHE_TTL
                        )
                    logger.info(f"Generated explanation via Claude for {model_name}")
                    return result
            
            # TRY OPENAI (SECONDARY)
            if OPENAI_AVAILABLE:
                result = AIExplanationService._generate_with_openai(
                    model_name, risk_score, fairness_score, drift_detected, policy_threshold
                )
                if result:
                    result["ai_source"] = "GPT-4 (OpenAI)"
                    result["is_real_ai"] = True
                    if use_cache:
                        get_cache().set(
                            f"ai_explanation:{model_name}:{risk_score:.2f}:{fairness_score:.4f}",
                            result,
                            AIExplanationService.CACHE_TTL
                        )
                    logger.info(f"Generated explanation via GPT-4 for {model_name}")
                    return result
            
            # FALLBACK: Intelligent template-based explanation
            logger.info("No AI backend available, using intelligent template")
            return AIExplanationService._generate_smart_fallback(
                model_name, risk_score, fairness_score, drift_detected, policy_threshold
            )
            
        except Exception as e:
            logger.error(f"Error generating AI explanation: {str(e)}")
            return AIExplanationService._generate_smart_fallback(
                model_name, risk_score, fairness_score, drift_detected, policy_threshold
            )
    
    @staticmethod
    def _generate_with_claude(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool,
        policy_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Generate explanation using Claude API"""
        try:
            client = anthropic.Anthropic()
            
            prompt = f"""Analyze this ML model governance situation and provide a brief, actionable explanation:

Model: {model_name}
Risk Score: {risk_score:.2f}/100
Fairness Disparity: {fairness_score:.4f}
Drift Detected: {drift_detected}
Policy Threshold: {policy_threshold}

Provide:
1. A concise 1-2 sentence summary of the current state
2. 2-3 specific actionable recommendations
3. Risk level assessment (low/medium/high/critical)

Keep response under 200 words. Be technical but accessible."""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            explanation_text = message.content[0].text if message.content else ""
            
            return {
                "explanation": explanation_text,
                "risk_level": AIExplanationService._assess_risk_level(risk_score, policy_threshold),
                "fairness_status": "acceptable" if fairness_score < 0.25 else "concerning",
                "drift_status": "detected" if drift_detected else "stable",
                "confidence": 0.95,
                "generated_at": datetime.utcnow().isoformat(),
                "model_version": "claude-3-5-sonnet",
                "is_real_ai": True
            }
        except Exception as e:
            logger.warning(f"Claude API error: {str(e)}")
            return None
    
    @staticmethod
    def _generate_with_openai(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool,
        policy_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Generate explanation using OpenAI API"""
        try:
            client = openai.OpenAI()
            
            prompt = f"""Analyze this ML model governance situation and provide a brief, actionable explanation:

Model: {model_name}
Risk Score: {risk_score:.2f}/100
Fairness Disparity: {fairness_score:.4f}
Drift Detected: {drift_detected}
Policy Threshold: {policy_threshold}

Provide:
1. A concise 1-2 sentence summary of the current state
2. 2-3 specific actionable recommendations
3. Risk level assessment (low/medium/high/critical)

Keep response under 200 words. Be technical but accessible."""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            explanation_text = response.choices[0].message.content if response.choices else ""
            
            return {
                "explanation": explanation_text,
                "risk_level": AIExplanationService._assess_risk_level(risk_score, policy_threshold),
                "fairness_status": "acceptable" if fairness_score < 0.25 else "concerning",
                "drift_status": "detected" if drift_detected else "stable",
                "confidence": 0.92,
                "generated_at": datetime.utcnow().isoformat(),
                "model_version": "gpt-4",
                "is_real_ai": True
            }
        except Exception as e:
            logger.warning(f"OpenAI API error: {str(e)}")
            return None
    
    @staticmethod
    def _assess_risk_level(risk_score: float, threshold: float) -> str:
        """Assess risk level based on score"""
        if risk_score >= threshold + 20:
            return "critical"
        elif risk_score >= threshold:
            return "high"
        elif risk_score >= threshold * 0.75:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _generate_smart_fallback(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool,
        policy_threshold: float
    ) -> Dict[str, Any]:
        """
        Generate intelligent template-based explanation.
        Much better than basic fallback - context-aware and detailed.
        """
        risk_level = AIExplanationService._assess_risk_level(risk_score, policy_threshold)
        fairness_status = "acceptable" if fairness_score < 0.25 else "concerning"
        
        # Context-aware explanation
        if risk_level == "critical":
            summary = f"Model '{model_name}' presents critical governance risk (score: {risk_score:.1f}). Immediate action required before deployment."
            recommendations = [
                "Perform comprehensive model retraining with balanced datasets",
                "Investigate recent input data distribution changes",
                "Review and strengthen fairness constraints"
            ]
        elif risk_level == "high":
            summary = f"Model '{model_name}' shows elevated risk (score: {risk_score:.1f}). Address concerns before production deployment."
            recommendations = [
                "Conduct thorough fairness audit across protected attributes",
                "Analyze feature importance and remove problematic signals",
                "Implement enhanced monitoring for production"
            ]
        elif risk_level == "medium":
            summary = f"Model '{model_name}' has moderate governance concerns (score: {risk_score:.1f}). Monitor closely during deployment."
            recommendations = [
                "Set up automated drift detection monitoring",
                "Schedule periodic fairness re-evaluation",
                "Document model behavior expectations"
            ]
        else:
            summary = f"Model '{model_name}' meets governance standards (score: {risk_score:.1f}). Ready for evaluation."
            recommendations = [
                "Establish baseline metrics for ongoing monitoring",
                "Document current model behavior and assumptions",
                "Plan quarterly compliance reviews"
            ]
        
        if drift_detected:
            recommendations.insert(0, "Address detected data drift before deployment")
        
        if fairness_status == "concerning":
            recommendations.insert(1, f"Investigate fairness disparity ({fairness_score:.4f}) across demographic groups")
        
        return {
            "explanation": summary,
            "risk_level": risk_level,
            "fairness_status": fairness_status,
            "drift_status": "detected" if drift_detected else "stable",
            "recommendations": recommendations,
            "confidence": 0.78,
            "generated_at": datetime.utcnow().isoformat(),
            "model_version": "intelligent-template",
            "is_real_ai": False,
            "ai_source": "Template",
            "note": "Using intelligent template-based explanation. Install RunAnywhere SDK or configure LLM APIs for real AI: ANTHROPIC_API_KEY or OPENAI_API_KEY"
        }
    
    @staticmethod
    def _generate_with_claude(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool,
        policy_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Generate explanation using Claude API"""
        try:
            client = anthropic.Anthropic()
            
            prompt = f"""Analyze this ML model governance situation and provide a brief, actionable explanation:

Model: {model_name}
Risk Score: {risk_score:.2f}/100
Fairness Disparity: {fairness_score:.4f}
Drift Detected: {drift_detected}
Policy Threshold: {policy_threshold}

Provide:
1. A concise 1-2 sentence summary of the current state
2. 2-3 specific actionable recommendations
3. Risk level assessment (low/medium/high/critical)

Keep response under 200 words. Be technical but accessible."""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            explanation_text = message.content[0].text if message.content else ""
            
            return {
                "explanation": explanation_text,
                "risk_level": AIExplanationService._assess_risk_level(risk_score, policy_threshold),
                "fairness_status": "acceptable" if fairness_score < 0.25 else "concerning",
                "drift_status": "detected" if drift_detected else "stable",
                "confidence": 0.95,
                "generated_at": datetime.utcnow().isoformat(),
                "model_version": "claude-3-5-sonnet",
                "is_real_ai": True
            }
        except Exception as e:
            logger.warning(f"Claude API error: {str(e)}")
            return None
    
    @staticmethod
    def _generate_with_openai(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool,
        policy_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Generate explanation using OpenAI API"""
        try:
            client = openai.OpenAI()
            
            prompt = f"""Analyze this ML model governance situation and provide a brief, actionable explanation:

Model: {model_name}
Risk Score: {risk_score:.2f}/100
Fairness Disparity: {fairness_score:.4f}
Drift Detected: {drift_detected}
Policy Threshold: {policy_threshold}

Provide:
1. A concise 1-2 sentence summary of the current state
2. 2-3 specific actionable recommendations
3. Risk level assessment (low/medium/high/critical)

Keep response under 200 words. Be technical but accessible."""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            explanation_text = response.choices[0].message.content if response.choices else ""
            
            return {
                "explanation": explanation_text,
                "risk_level": AIExplanationService._assess_risk_level(risk_score, policy_threshold),
                "fairness_status": "acceptable" if fairness_score < 0.25 else "concerning",
                "drift_status": "detected" if drift_detected else "stable",
                "confidence": 0.92,
                "generated_at": datetime.utcnow().isoformat(),
                "model_version": "gpt-4",
                "is_real_ai": True
            }
        except Exception as e:
            logger.warning(f"OpenAI API error: {str(e)}")
            return None
    
    @staticmethod
    def _assess_risk_level(risk_score: float, threshold: float) -> str:
        """Assess risk level based on score"""
        if risk_score >= threshold + 20:
            return "critical"
        elif risk_score >= threshold:
            return "high"
        elif risk_score >= threshold * 0.75:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _generate_smart_fallback(
        model_name: str,
        risk_score: float,
        fairness_score: float,
        drift_detected: bool,
        policy_threshold: float
    ) -> Dict[str, Any]:
        """
        Generate intelligent template-based explanation.
        Much better than basic fallback - context-aware and detailed.
        """
        risk_level = AIExplanationService._assess_risk_level(risk_score, policy_threshold)
        fairness_status = "acceptable" if fairness_score < 0.25 else "concerning"
        
        # Context-aware explanation
        if risk_level == "critical":
            summary = f"Model '{model_name}' presents critical governance risk (score: {risk_score:.1f}). Immediate action required before deployment."
            recommendations = [
                "Perform comprehensive model retraining with balanced datasets",
                "Investigate recent input data distribution changes",
                "Review and strengthen fairness constraints"
            ]
        elif risk_level == "high":
            summary = f"Model '{model_name}' shows elevated risk (score: {risk_score:.1f}). Address concerns before production deployment."
            recommendations = [
                "Conduct thorough fairness audit across protected attributes",
                "Analyze feature importance and remove problematic signals",
                "Implement enhanced monitoring for production"
            ]
        elif risk_level == "medium":
            summary = f"Model '{model_name}' has moderate governance concerns (score: {risk_score:.1f}). Monitor closely during deployment."
            recommendations = [
                "Set up automated drift detection monitoring",
                "Schedule periodic fairness re-evaluation",
                "Document model behavior expectations"
            ]
        else:
            summary = f"Model '{model_name}' meets governance standards (score: {risk_score:.1f}). Ready for evaluation."
            recommendations = [
                "Establish baseline metrics for ongoing monitoring",
                "Document current model behavior and assumptions",
                "Plan quarterly compliance reviews"
            ]
        
        if drift_detected:
            recommendations.insert(0, "Address detected data drift before deployment")
        
        if fairness_status == "concerning":
            recommendations.insert(1, f"Investigate fairness disparity ({fairness_score:.4f}) across demographic groups")
        
        return {
            "explanation": summary,
            "risk_level": risk_level,
            "fairness_status": fairness_status,
            "drift_status": "detected" if drift_detected else "stable",
            "recommendations": recommendations,
            "confidence": 0.78,
            "generated_at": datetime.utcnow().isoformat(),
            "model_version": "intelligent-template",
            "is_real_ai": False,
            "note": "Using intelligent template-based explanation. Install LLM API keys for real AI: ANTHROPIC_API_KEY or OPENAI_API_KEY"
        }
