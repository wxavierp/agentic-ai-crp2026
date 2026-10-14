"""Offline tests for the OpenAI-compat fixes in utils/llm_client.py (no network, no key)."""
import sys, os, types
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from utils.llm_client import LLMClient

class _Msg:
    content = "hi"; tool_calls = None
class _Resp:
    choices = [types.SimpleNamespace(message=_Msg())]

class FakeCompletions:
    def __init__(self, rules): self.calls, self.rules = [], rules
    def create(self, **kw):
        self.calls.append(dict(kw))
        for bad_key, text in self.rules:
            if bad_key in kw:
                raise RuntimeError(text)
        return _Resp()

def make(rules, provider="openai"):
    c = LLMClient.__new__(LLMClient)
    c.provider = provider
    c.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=FakeCompletions(rules)))
    return c

def test_plain_model_untouched():
    os.environ.pop("LLM_REASONING_EFFORT", None)
    c = make([])
    c.chat([{"role": "user", "content": "x"}])
    kw = c.client.chat.completions.calls[0]
    assert "max_tokens" in kw and "temperature" in kw and "reasoning_effort" not in kw

def test_reasoning_effort_only_when_set_and_openai():
    os.environ["LLM_REASONING_EFFORT"] = "none"
    try:
        c = make([]); c.chat([{"role": "user", "content": "x"}])
        assert c.client.chat.completions.calls[0]["reasoning_effort"] == "none"
        g = make([], provider="groq"); g.chat([{"role": "user", "content": "x"}])
        assert "reasoning_effort" not in g.client.chat.completions.calls[0]
    finally:
        os.environ.pop("LLM_REASONING_EFFORT", None)

def test_max_tokens_swap_is_remembered():
    c = make([("max_tokens", "Unsupported parameter: 'max_tokens'. Use 'max_completion_tokens' instead.")])
    r = c.chat([{"role": "user", "content": "x"}])
    assert r.text == "hi"
    calls = c.client.chat.completions.calls
    assert len(calls) == 2 and "max_completion_tokens" in calls[1] and "max_tokens" not in calls[1]
    c.chat([{"role": "user", "content": "y"}])
    assert len(c.client.chat.completions.calls) == 3          # no extra failed attempt the 2nd time

def test_temperature_dropped():
    c = make([("temperature", "Unsupported value: 'temperature' does not support 0.0 with this model. Only the default (1) value is supported.")])
    assert c.chat([{"role": "user", "content": "x"}]).text == "hi"
    assert "temperature" not in c.client.chat.completions.calls[-1]

def test_other_errors_still_raise():
    c = make([("model", "invalid api key")])
    try:
        c.chat([{"role": "user", "content": "x"}], model="m")
    except RuntimeError as e:
        assert "api key" in str(e)
    else:
        raise AssertionError("should raise")

if __name__ == "__main__":
    n = 0
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); n += 1; print("ok", k)
    print(f"{n} passed")
