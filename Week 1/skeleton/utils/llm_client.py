"""
Unified LLM client for the BITS Agentic AI Engineering course.

Supports OpenAI, Groq, Anthropic and Google Gemini behind ONE simple interface.
You only need to install the SDK for the provider you actually use (see SETUP.md).

Pick your provider in either of two ways:
  1. Set LLM_PROVIDER in your .env  (e.g. LLM_PROVIDER=groq), or
  2. Pass it in code:  client = LLMClient(provider="groq")

Groq and Google Gemini both have generous FREE tiers — great for this course.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Default model per provider. Override any of these with LLM_MODEL in your .env.
DEFAULT_MODELS = {
    "openai":    "gpt-4o-mini",
    "groq":      "llama-3.3-70b-versatile",
    "anthropic": "claude-3-5-haiku-latest",
    "google":    "gemini-2.0-flash",
}


class LLMClient:
    """A thin, provider-agnostic wrapper around chat LLMs."""

    def __init__(self, provider=None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif self.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.client = genai
        else:
            raise ValueError(
                f"Unsupported provider: {self.provider!r}. "
                "Choose from: openai, groq, anthropic, google."
            )

    def _default_model(self):
        return os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(self.provider, "gpt-4o-mini")

    def get_completion(self, prompt, system_message=None, temperature=0.7,
                       max_tokens=600, model=None):
        """
        Send a single prompt and get back the text reply (a str), or None on error.

        Args:
            prompt (str):          The user message.
            system_message (str):  Optional instructions / persona.
            temperature (float):   0.0 = focused, 1.0 = creative.
            max_tokens (int):      Cap on the reply length.
            model (str):           Override the default model for this call.
        """
        model = model or self._default_model()
        try:
            # --- OpenAI & Groq share the same chat-completions API ---
            if self.provider in ("openai", "groq"):
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                resp = self.client.chat.completions.create(
                    model=model, messages=messages,
                    temperature=temperature, max_tokens=max_tokens,
                )
                return resp.choices[0].message.content

            # --- Anthropic (Claude) ---
            elif self.provider == "anthropic":
                kwargs = {
                    "model": model, "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system_message:
                    kwargs["system"] = system_message
                resp = self.client.messages.create(**kwargs)
                return resp.content[0].text

            # --- Google Gemini ---
            elif self.provider == "google":
                gen_model = self.client.GenerativeModel(
                    model_name=model,
                    system_instruction=system_message,
                )
                resp = gen_model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )
                return resp.text

        except Exception as e:
            print(f"[LLMClient] Error from provider '{self.provider}': {e}")
            return None
