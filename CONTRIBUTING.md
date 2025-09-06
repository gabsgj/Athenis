# Contributing

Thanks for your interest in contributing!

## Setup
- Python 3.10+
- Go 1.22+

## Extending Prompt Templates
- Edit `app/models/prompt_manager.py` to add new templates or tweak phrasing.
- Ensure the `build` method handles new tasks.

## Adding Models
- Update environment variable `MODEL_NAME`.
- If the model is not chat-instruction-tuned, adjust prompts accordingly.
- To add a new embedding model, set `EMBEDDING_MODEL`.

## Tests
- Run `make test`.
- Add unit tests under `tests/`.

## Code Style
- Python: black/isort/flake8.
- Go: `gofmt` and `go test`.

## Issues & PRs
- Describe the change and rationale.
- Include before/after or sample outputs when relevant.
