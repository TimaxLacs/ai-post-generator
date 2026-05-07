import os
from typing import Tuple, Optional
from openai import AsyncOpenAI, OpenAIError

class AIPipeline:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: str = "https://openrouter.ai/api/v1",
        gen_model: str = "google/gemini-2.0-flash-lite-preview-02-05:free",
        mod_model: str = "google/gemini-2.0-flash-lite-preview-02-05:free"
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in OPENROUTER_API_KEY environment variable")
            
        self.client = AsyncOpenAI(
            api_key=self.api_key, 
            base_url=base_url,
            timeout=30.0,
            max_retries=3
        )
        self.gen_model = gen_model
        self.mod_model = mod_model
        
        self.gen_sys = "You are a professional social media manager. Write an engaging post based on the context."
        self.mod_sys = "You are a strict editor. Reply EXACTLY with 'APPROVED' if the post is perfect. Otherwise, write constructive feedback."

    async def close(self) -> None:
        if hasattr(self.client, "close") and callable(self.client.close):
            await self.client.close()

    async def _call_api(self, model: str, system_prompt: str, user_prompt: str, error_context: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content or ""
        except OpenAIError as e:
            raise RuntimeError(f"Error during {error_context}: {str(e)}") from e

    async def generate(self, context: str, feedback_history: str = "") -> str:
        prompt = f"Context:\n{context}\n\n"
        if feedback_history:
            prompt += f"Previous Feedback:\n{feedback_history}\nPlease fix the issues and rewrite."
            
        return await self._call_api(
            model=self.gen_model, 
            system_prompt=self.gen_sys, 
            user_prompt=prompt, 
            error_context="generation"
        )

    async def moderate(self, draft: str) -> str:
        return await self._call_api(
            model=self.mod_model, 
            system_prompt=self.mod_sys, 
            user_prompt=draft, 
            error_context="moderation"
        )

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
