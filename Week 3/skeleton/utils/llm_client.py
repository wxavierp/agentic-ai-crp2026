"""
Unified LLM client for the BITS Agentic AI Engineering course — Week 2 edition.

This is the Week 1 client PLUS one new method, `chat()`, that supports native
TOOL / FUNCTION CALLING. Everything from Week 1 (get_completion) still works
unchanged, so older lesson scripts keep running.

Pick your provider in either of two ways:
  1. Set LLM_PROVIDER in your .env  (e.g. LLM_PROVIDER=groq), or
  2. Pass it in code:  client = LLMClient(provider="groq")

TOOL CALLING NOTE (important for Week 2):
  The `chat()` method uses the OpenAI-style tools API, which is spoken by
  OpenAI, Groq, and local Ollama. Groq's FREE tier supports it and is the
  recommended default for this course. Anthropic and Google Gemini also do
  tool calling, but with a *different* request/response shape — so for the
  Week 2 labs use LLM_PROVIDER=openai, groq, or ollama.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Default model per provider. Override any of these with LLM_MODEL in your .env.
DEFAULT_MODELS = {
    "openai":    "gpt-4o-mini",
    "groq":      "llama-3.3-70b-versatile",
    "anthropic": "claude-3-5-haiku-latest",
    "google":    "gemini-2.0-flash",
    "ollama":    "llama3.1",
}

# Providers that speak the OpenAI-style chat/tools API (so chat() works).
OPENAI_STYLE = ("openai", "groq", "ollama")


class ToolCall:
    """
    A tidy, provider-agnostic view of ONE tool call the model asked for.

    Attributes:
        id (str):     the call id (send it back with the tool result)
        name (str):   the tool/function name the model chose
        arguments (dict): the parsed JSON arguments (already a Python dict)
        raw:          the original SDK object (only needed for advanced use)
    """
    def __init__(self, id, name, arguments, raw=None):
        self.id = id
        self.name = name
        self.arguments = arguments
        self.raw = raw

    def __repr__(self):
        return f"ToolCall(name={self.name!r}, arguments={self.arguments!r})"


class ChatResult:
    """
    A tidy view of the model's reply to chat().

    Attributes:
        text (str | None):        the assistant's text answer, if any
        tool_calls (list[ToolCall]): tools the model wants to run (may be empty)
        raw_message:              the original SDK message (append to history)
    """
    def __init__(self, text, tool_calls, raw_message):
        self.text = text
        self.tool_calls = tool_calls
        self.raw_message = raw_message

    @property
    def wants_tools(self):
        return len(self.tool_calls) > 0


class LLMClient:
    """A thin, provider-agnostic wrapper around chat LLMs (with tool calling)."""

    def __init__(self, provider=None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        elif self.provider == "ollama":
            # Ollama exposes an OpenAI-compatible endpoint, so we reuse the SDK.
            from openai import OpenAI
            self.client = OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama",  # any non-empty string
            )
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
                "Choose from: openai, groq, ollama, anthropic, google."
            )

    def _default_model(self):
        return os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(self.provider, "gpt-4o-mini")

    # ------------------------------------------------------------------ #
    #  Week 1 method — a single prompt in, a single string out.          #
    # ------------------------------------------------------------------ #
    def get_completion(self, prompt, system_message=None, temperature=0.7,
                       max_tokens=600, model=None):
        """Send a single prompt and get back the text reply (a str), or None on error."""
        model = model or self._default_model()
        try:
            if self.provider in ("openai", "groq", "ollama"):
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                resp = self.client.chat.completions.create(
                    model=model, messages=messages,
                    temperature=temperature, max_tokens=max_tokens,
                )
                return resp.choices[0].message.content

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

            elif self.provider == "google":
                gen_model = self.client.GenerativeModel(
                    model_name=model, system_instruction=system_message)
                resp = gen_model.generate_content(
                    prompt, generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens})
                return resp.text

        except Exception as e:
            print(f"[LLMClient] Error from provider '{self.provider}': {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Week 2 method — messages + tools in, a ChatResult out.            #
    # ------------------------------------------------------------------ #
    def chat(self, messages, tools=None, tool_choice="auto",
             temperature=0.0, max_tokens=700, model=None):
        """
        One turn of a tool-calling conversation.

        Args:
            messages (list[dict]): the running conversation. Each item is a dict
                like {"role": "user"/"system"/"assistant"/"tool", "content": ...}.
                (For a tool result, also include "tool_call_id".)
            tools (list[dict] | None): OpenAI-style tool schemas (see the lessons).
            tool_choice: "auto" (model decides), "none", or {"type": "function",
                "function": {"name": "..."}} to force a specific tool.
            temperature (float): 0.0 is best for reliable tool use.

        Returns:
            ChatResult with .text, .tool_calls (list[ToolCall]) and .raw_message.

        Raises:
            NotImplementedError for anthropic/google (use openai/groq/ollama in Week 2).
        """
        if self.provider not in OPENAI_STYLE:
            raise NotImplementedError(
                f"chat() tool calling is wired for {OPENAI_STYLE} in this course. "
                f"You set LLM_PROVIDER={self.provider!r}. For the Week 2 labs, use "
                "LLM_PROVIDER=groq (free) or openai or ollama."
            )

        model = model or self._default_model()
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        # Normalise the tool calls into simple ToolCall objects.
        tool_calls = []
        for tc in (getattr(msg, "tool_calls", None) or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                # The model produced invalid JSON — hand it back as a raw string
                # so the lesson can show how to handle (validate) bad arguments.
                args = {"_raw": tc.function.arguments, "_error": "invalid_json"}
            tool_calls.append(
                ToolCall(id=tc.id, name=tc.function.name, arguments=args, raw=tc)
            )

        return ChatResult(text=msg.content, tool_calls=tool_calls, raw_message=msg)
