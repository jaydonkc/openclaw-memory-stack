# Contributing

Thanks for contributing to OpenClaw Memory Stack.

## Development setup

```bash
bash scripts/setup.sh
bash scripts/doctor.sh
```

## Validation before PR

```bash
scripts/run-python.sh scripts/index_shared_memory.py --scope coding
scripts/run-python.sh scripts/query_memory.py --scope coding --q "test query"
```

## Pull requests

- Keep changes focused and small.
- Update README/docs when behavior changes.
- Include migration notes for schema/vector-dimension changes.
