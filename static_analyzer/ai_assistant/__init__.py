"""AI Assistant for providing explanations and suggestions."""

import os
from typing import Optional, Dict, Any, List
from ..models import Violation


class AIAssistant:
    """AI assistant for generating explanations and fix suggestions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AI assistant.
        
        Args:
            config: AI configuration dictionary
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        
        if self.enabled:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client if enabled."""
        if not self.enabled:
            return
        
        try:
            import openai
            
            api_key_env = self.config.get("api_key_env", "OPENAI_API_KEY")
            api_key = os.getenv(api_key_env)
            
            if not api_key:
                print(f"Warning: {api_key_env} not found. AI assistant disabled.")
                self.enabled = False
                return
            
            self.client = openai.OpenAI(api_key=api_key)
            
        except ImportError:
            print("Warning: openai package not installed. AI assistant disabled.")
            self.enabled = False
        except Exception as e:
            print(f"Warning: Failed to initialize AI client: {str(e)}. AI assistant disabled.")
            self.enabled = False
    
    def enhance_violations(self, violations: List[Violation]) -> List[Violation]:
        """Enhance violations with AI-generated explanations.
        
        Args:
            violations: List of violations to enhance
            
        Returns:
            List of enhanced violations
        """
        if not self.enabled:
            return violations
        
        enhanced_violations = []
        
        for violation in violations:
            try:
                enhanced = self._enhance_single_violation(violation)
                enhanced_violations.append(enhanced)
            except Exception as e:
                print(f"Warning: Failed to enhance violation {violation.rule_id}: {str(e)}")
                enhanced_violations.append(violation)
        
        return enhanced_violations
    
    def _enhance_single_violation(self, violation: Violation) -> Violation:
        """Enhance a single violation with AI explanations.
        
        Args:
            violation: Violation to enhance
            
        Returns:
            Enhanced violation
        """
        if not self.enabled:
            return violation
        
        # Generate AI explanation
        explanation = self._generate_explanation(violation)
        risk_summary = self._generate_risk_summary(violation)
        suggested_fix = self._generate_fix_suggestion(violation)
        
        # Create enhanced violation (since Violation is frozen, create new one)
        enhanced_violation = Violation(
            rule_id=violation.rule_id,
            standard=violation.standard,
            location=violation.location,
            message=violation.message,
            severity=violation.severity,
            confidence=violation.confidence,
            source_context=violation.source_context,
            metadata=violation.metadata,
            ai_explanation=explanation,
            ai_risk_summary=risk_summary,
            ai_suggested_fix=suggested_fix
        )
        
        return enhanced_violation
    
    def _generate_explanation(self, violation: Violation) -> Optional[str]:
        """Generate human-readable explanation for a violation.
        
        Args:
            violation: Violation to explain
            
        Returns:
            AI-generated explanation
        """
        prompt = self._build_explanation_prompt(violation)
        return self._call_ai(prompt, "explanation")
    
    def _generate_risk_summary(self, violation: Violation) -> Optional[str]:
        """Generate risk summary for a violation.
        
        Args:
            violation: Violation to analyze
            
        Returns:
            AI-generated risk summary
        """
        prompt = self._build_risk_prompt(violation)
        return self._call_ai(prompt, "risk_summary")
    
    def _generate_fix_suggestion(self, violation: Violation) -> Optional[str]:
        """Generate fix suggestion for a violation.
        
        Args:
            violation: Violation to fix
            
        Returns:
            AI-generated fix suggestion
        """
        prompt = self._build_fix_prompt(violation)
        return self._call_ai(prompt, "fix_suggestion")
    
    def _build_explanation_prompt(self, violation: Violation) -> str:
        """Build prompt for explanation generation."""
        return f"""
You are a senior embedded systems engineer explaining static analysis violations to developers.

VIOLATION DETAILS:
- Rule: {violation.rule_id}
- Standard: {violation.standard.value}
- Location: {violation.location}
- Message: {violation.message}
- Severity: {violation.severity.value}

SOURCE CODE:
{violation.source_context or "Source context not available"}

TASK: Provide a clear, concise explanation of why this violation matters for embedded C/C++ development. Focus on:
1. What the rule is trying to prevent
2. Why it's important for embedded systems
3. Potential consequences if ignored

Keep the explanation under 150 words and suitable for intermediate developers.
"""
    
    def _build_risk_prompt(self, violation: Violation) -> str:
        """Build prompt for risk analysis."""
        return f"""
You are a safety-critical systems expert analyzing code risks.

VIOLATION DETAILS:
- Rule: {violation.rule_id}
- Standard: {violation.standard.value}
- Location: {violation.location}
- Message: {violation.message}
- Severity: {violation.severity.value}

SOURCE CODE:
{violation.source_context or "Source context not available"}

TASK: Provide a risk assessment focusing on:
1. Potential runtime failures
2. Security implications
3. Safety concerns for automotive/embedded systems
4. Impact on system reliability

Provide a concise risk summary under 100 words.
"""
    
    def _build_fix_prompt(self, violation: Violation) -> str:
        """Build prompt for fix suggestions."""
        return f"""
You are an expert C/C++ developer providing code fix suggestions.

VIOLATION DETAILS:
- Rule: {violation.rule_id}
- Standard: {violation.standard.value}
- Location: {violation.location}
- Message: {violation.message}

SOURCE CODE:
{violation.source_context or "Source context not available"}

TASK: Suggest specific code changes to fix this violation. Provide:
1. Corrected code snippet
2. Brief explanation of the change
3. Any additional considerations

Focus on minimal, safe changes that address the violation while maintaining functionality.
Keep suggestions under 200 words.
"""
    
    def _call_ai(self, prompt: str, request_type: str) -> Optional[str]:
        """Make AI API call.
        
        Args:
            prompt: Prompt text
            request_type: Type of request for logging
            
        Returns:
            AI response text
        """
        if not self.enabled:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4"),
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert in embedded systems and static code analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.get("max_tokens", 500),
                temperature=self.config.get("temperature", 0.1)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Warning: AI call failed for {request_type}: {str(e)}")
            return None


class MockAIAssistant:
    """Mock AI assistant for testing without API calls."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock AI assistant."""
        self.config = config
        self.enabled = True  # Always enabled for testing
    
    def enhance_violations(self, violations: List[Violation]) -> List[Violation]:
        """Mock enhancement of violations."""
        enhanced_violations = []
        
        for violation in violations:
            enhanced = Violation(
                rule_id=violation.rule_id,
                standard=violation.standard,
                location=violation.location,
                message=violation.message,
                severity=violation.severity,
                confidence=violation.confidence,
                source_context=violation.source_context,
                metadata=violation.metadata,
                ai_explanation=f"Mock explanation for {violation.rule_id}: This violation occurs when the code doesn't follow best practices for embedded systems development.",
                ai_risk_summary=f"Mock risk summary: This could lead to runtime issues, security vulnerabilities, or safety concerns in embedded environments.",
                ai_suggested_fix=f"Mock fix suggestion: Refactor the code to comply with {violation.rule_id} by following the standard's guidelines."
            )
            enhanced_violations.append(enhanced)
        
        return enhanced_violations


def create_ai_assistant(config: Dict[str, Any], mock: bool = False) -> AIAssistant:
    """Factory function to create AI assistant.
    
    Args:
        config: AI configuration
        mock: Whether to create mock assistant
        
    Returns:
        AI assistant instance
    """
    if mock:
        return MockAIAssistant(config)
    else:
        return AIAssistant(config)
