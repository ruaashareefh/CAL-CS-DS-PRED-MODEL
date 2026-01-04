"""
LLM-based analysis of student notes using Groq API.

Uses Groq's free Llama 3.1 8B model to extract academic context factors
from free-form student notes.

PRIVACY WARNING:
- Notes are sent to Groq's third-party API for processing
- Groq may process but should not retain data per their TOS
- Users must be informed and consent before sending notes
"""
import os
import json
import logging
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class GroqAnalyzer:
    """
    Analyzes student notes using Groq's Llama 3.1 model to extract
    contextual factors affecting academic performance.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq analyzer.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Fast, free model
        self.timeout = 10.0  # 10 second timeout

    def _build_system_prompt(self) -> str:
        """
        Build system prompt for academic context extraction.

        Returns detailed instructions for the LLM on how to analyze notes.
        """
        return """You are an academic performance analyzer. Your job is to extract relevant contextual factors from a student's free-form notes that might affect their performance in a course.

Analyze the student's notes and extract ONLY the following factors (if mentioned):
1. Health issues or disabilities affecting study (physical/mental health)
2. Major life events or personal circumstances (family, relationships, housing)
3. Work or external commitments (job hours, caregiving, extracurriculars)
4. Specific academic strengths or weaknesses (subject areas, learning styles)
5. Motivation level and interest in the subject
6. Prior relevant experience outside of coursework
7. Study group or peer support availability
8. Access to resources (tutoring, office hours, textbooks)

Output ONLY a JSON object with these fields (use null if not mentioned):
{
  "health_impact": "positive" | "negative" | "neutral" | null,
  "external_commitments": "high" | "moderate" | "low" | null,
  "motivation": "high" | "moderate" | "low" | null,
  "relevant_experience": "extensive" | "some" | "none" | null,
  "support_system": "strong" | "moderate" | "weak" | null,
  "resource_access": "full" | "limited" | "restricted" | null,
  "confidence_adjustment": -0.2 to +0.2,
  "reasoning": "1-2 sentence summary"
}

The confidence_adjustment is a GPA modifier between -0.2 and +0.2 based on the overall context.
Be conservative - most contexts should result in adjustments between -0.1 and +0.1.

Output ONLY the JSON, no other text."""

    def _build_user_prompt(self, notes: str, course_name: str) -> str:
        """
        Build user prompt with student notes and course context.

        Args:
            notes: Student's free-form notes
            course_name: Target course (e.g., "COMPSCI 170")

        Returns:
            Formatted prompt string
        """
        return f"""Target Course: {course_name}

Student Notes:
{notes}

Analyze the above notes and extract relevant contextual factors as JSON."""

    async def analyze_notes(
        self,
        notes: str,
        course_name: str = "the course"
    ) -> Dict:
        """
        Analyze student notes using Groq LLM.

        Args:
            notes: Student's free-form notes
            course_name: Target course name

        Returns:
            dict with extracted factors and confidence adjustment
            Returns default values if API fails or no API key

        Example return:
        {
            'health_impact': 'negative',
            'motivation': 'high',
            'confidence_adjustment': -0.05,
            'reasoning': 'Recent illness but high motivation',
            'llm_used': True
        }
        """
        # Return neutral if no API key configured
        if not self.api_key:
            logger.warning("No Groq API key configured, skipping LLM analysis")
            return self._get_default_response(used_llm=False)

        # Return neutral if notes are too short
        if not notes or len(notes.strip()) < 10:
            logger.info("Notes too short for LLM analysis")
            return self._get_default_response(used_llm=False)

        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(notes, course_name)

            # Call Groq API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,  # Low temperature for consistent extraction
                        "max_tokens": 300,
                        "top_p": 0.9
                    }
                )

            # Check response
            if response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return self._get_default_response(used_llm=False)

            # Parse response
            data = response.json()
            content = data['choices'][0]['message']['content']

            # Extract JSON from response
            result = self._parse_llm_response(content)
            result['llm_used'] = True

            logger.info(f"LLM analysis complete: adjustment={result.get('confidence_adjustment')}")
            return result

        except httpx.TimeoutException:
            logger.error("Groq API timeout")
            return self._get_default_response(used_llm=False)
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            return self._get_default_response(used_llm=False)

    def _parse_llm_response(self, content: str) -> Dict:
        """
        Parse LLM response and extract JSON.

        Args:
            content: Raw LLM response text

        Returns:
            Parsed dict with extracted factors
        """
        try:
            # Try to find JSON in response
            start = content.find('{')
            end = content.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = content[start:end]
                result = json.loads(json_str)

                # Validate and clean result
                result = self._validate_result(result)
                return result
            else:
                logger.warning("No JSON found in LLM response")
                return self._get_default_response(used_llm=True)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            return self._get_default_response(used_llm=True)

    def _validate_result(self, result: Dict) -> Dict:
        """
        Validate and clean LLM result.

        Args:
            result: Raw parsed result from LLM

        Returns:
            Validated and cleaned result
        """
        # Ensure confidence_adjustment is in valid range
        adjustment = result.get('confidence_adjustment', 0.0)
        if not isinstance(adjustment, (int, float)):
            adjustment = 0.0
        adjustment = max(-0.2, min(0.2, float(adjustment)))
        result['confidence_adjustment'] = adjustment

        # Ensure reasoning exists
        if 'reasoning' not in result or not result['reasoning']:
            result['reasoning'] = "Analysis based on provided context"

        return result

    def _get_default_response(self, used_llm: bool = False) -> Dict:
        """
        Get default neutral response when LLM is not used or fails.

        Args:
            used_llm: Whether LLM was attempted

        Returns:
            Default neutral response
        """
        return {
            'health_impact': None,
            'external_commitments': None,
            'motivation': None,
            'relevant_experience': None,
            'support_system': None,
            'resource_access': None,
            'confidence_adjustment': 0.0,
            'reasoning': 'No additional context analyzed' if not used_llm else 'Unable to analyze context',
            'llm_used': used_llm
        }


# Singleton instance
_groq_analyzer = None


def get_groq_analyzer() -> GroqAnalyzer:
    """
    Get singleton Groq analyzer instance.

    Returns:
        GroqAnalyzer instance
    """
    global _groq_analyzer
    if _groq_analyzer is None:
        _groq_analyzer = GroqAnalyzer()
    return _groq_analyzer
