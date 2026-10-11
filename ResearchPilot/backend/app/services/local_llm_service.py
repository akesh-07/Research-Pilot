from openai import OpenAI
import json
from app.core.logging import logger

class LocalLLMService:
    def __init__(self):
        # LM Studio exposes an OpenAI-compatible API on port 1234 by default.
        logger.info("Connecting to LM Studio Local Server...")
        self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    def generate_json_response(self, prompt: str) -> dict:
        try:
            logger.info("Asking LM Studio...")
            
            response = self.client.chat.completions.create(
                model="qwen_qwen3-8b", # The exact identifier from LM Studio
                messages=[
                    {"role": "system", "content": "You are a data pipeline. You MUST output ONLY valid JSON. No markdown formatting, no explanations, no text before or after the JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6
            )
            
            content = response.choices[0].message.content.strip()
            # Strip markdown formatting just in case the model wraps it
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            content = content.strip()
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error calling LM Studio: {e}")
            raise e

local_llm_service = LocalLLMService()
