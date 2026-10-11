# Project conventions

Preserve raw complaint narratives under ignored `data/private/` only. Public artifacts may contain aggregates, safe lexicon model weights, and anonymous review metadata, never complaint IDs or verbatim text. Use `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest`. Rebuild measured artifacts only from the frozen private sample. Synthetic tests never supply dashboard results.
