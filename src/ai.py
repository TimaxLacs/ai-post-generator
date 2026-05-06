import os
from typing import Tuple, Optional
from openai import AsyncOpenAI, OpenAIError

class AIPipeline:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in OPENROUTER_API_KEY environment variable")
            
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)
        self.gen_model = "openai/gpt-4o-mini"
        self.mod_model = "openai/gpt-4o"
        
        self.gen_sys = "You are a professional social media manager. Write an engaging post based on the context."
        self.mod_sys = "You are a strict editor. Reply EXACTLY with 'APPROVED' if the post is perfect. Otherwise, write constructive feedback."

    async def generate(self, context: str, feedback_history: str = "") -> str:
        prompt = f"Context:\n{context}\n\n"
        if feedback_history:
            prompt += f"Previous Feedback:\n{feedback_history}\nPlease fix the issues and rewrite."
            
        try:
            response = await self.client.chat.completions.create(
                model=self.gen_model,
                messages=[
                    {"role": "system", "content": self.gen_sys},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content or ""
        except OpenAIError as e:
            raise RuntimeError(f"Error during generation: {str(e)}") from e

    async def moderate(self, draft: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.mod_model,
                messages=[
                    {"role": "system", "content": self.mod_sys},
                    {"role": "user", "content": draft}
                ]
            )
            return response.choices[0].message.content or ""
        except OpenAIError as e:
            raise RuntimeError(f"Error during moderation: {str(e)}") from e

    async def process_block(self, context: str) -> Tuple[bool, str, Optional[str]]:
        if not context or not context.strip():
            raise ValueError("Context cannot be empty")

        feedback_history = ""
        draft = ""
        feedback = ""
        
        for i in range(3):
            draft = await self.generate(context, feedback_history)
            feedback = await self.moderate(draft)
            
            is_approved = feedback.strip().upper() == "APPROVED"
            if is_approved:
                return True, draft, None
                
            feedback_history += f"\nAttempt {i+1} feedback: {feedback}"
            
        return False, draft, feedback
