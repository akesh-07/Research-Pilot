import google.generativeai as genai
from google.generativeai.types import generation_types
from app.core.config import settings
from app.core.logging import logger
import json

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
            
        system_instruction = (
            "You are ResearchPilot AI, an expert research intelligence system strictly and exclusively "
            "specialized in biomedical, biochemical, and pharmaceutical drug discovery research. "
            "CRITICAL ADHERENCE CONSTRAINT: You must ALWAYS stay strictly within the exact scope of the "
            "user's research prompt. All generated tasks, paper summaries, extracted points, and syntheses "
            "must be directly and specifically relevant ONLY to what research the user requested. "
            "Never deviate into unrelated diseases, unrequested targets, or generic scientific trivia. "
            "You MUST output ONLY valid JSON."
        )
        self.model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=system_instruction
        )

    def generate_json_response(self, prompt: str) -> dict:
        if not self.api_key:
            raise Exception("Gemini API key is missing.")
            
        try:
            # Requesting JSON structure using response_mime_type if supported, or via prompt
            # gemini-1.5/2.5 series supports response_mime_type="application/json"
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise e

gemini_service = GeminiService()
