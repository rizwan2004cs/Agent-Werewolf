"""Model layer — LangChain ChatOpenAI, the ONLY module that calls the model.

Works with any OpenAI-compatible endpoint (OpenAI, Groq, ...). chat() walks the
configured fallback CHAIN (config.models) in order: primary model, smaller
same-provider model, then a different provider entirely (e.g. Groq -> OpenAI).
So when one endpoint is rate-limited (e.g. Groq's daily token cap) we keep
producing real dialogue from the next one, and only fall to canned mock lines
if every endpoint fails.

Clients are built lazily and cached, so importing this module never needs a key.
"""
from ..config import config

# id(endpoint dict) + json_mode -> ChatOpenAI
_clients: dict[tuple[int, bool], object] = {}


def _client(endpoint: dict, json_mode: bool):
    key = (id(endpoint), json_mode)
    if key not in _clients:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": endpoint["model"],
            "api_key": endpoint["api_key"],
            # Bound every request so a stalled call can never freeze the game.
            "timeout": 20,
            # Fail fast: don't burn time retrying a rate-limited endpoint — the
            # fallback chain below handles recovery instead.
            "max_retries": 0,
        }
        if endpoint.get("base_url"):
            kwargs["base_url"] = endpoint["base_url"]
        if json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
        _clients[key] = ChatOpenAI(**kwargs)
    return _clients[key]


def chat(prompt: str, max_tokens: int = 220, json_mode: bool = False) -> str:
    from langchain_core.messages import HumanMessage

    chain = config.models
    last_err: Exception | None = None
    for i, endpoint in enumerate(chain):
        try:
            model = _client(endpoint, json_mode).bind(max_tokens=max_tokens)
            resp = model.invoke([HumanMessage(content=prompt)])
            content = resp.content
            if isinstance(content, list):  # some providers return content blocks
                content = "".join(str(c) for c in content)
            text = (content or "").strip()
            if text:
                return text
        except Exception as e:  # try the next endpoint (e.g. on a 429 rate limit)
            last_err = e
            if i + 1 < len(chain):
                nxt = chain[i + 1]
                print(
                    f"[llm] {endpoint['provider']}:{endpoint['model']} failed ({e}); "
                    f"falling back to {nxt['provider']}:{nxt['model']}"
                )
            continue
    raise last_err or RuntimeError("no model produced output")
