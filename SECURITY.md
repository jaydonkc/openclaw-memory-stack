# Security Policy

## Reporting a vulnerability

Please open a private security advisory on GitHub or contact the maintainer directly.

Include:
- affected file/path
- reproduction steps
- impact assessment
- suggested mitigation (if available)

## Operational security notes

- Do not commit API keys or tokens.
- Keep `.env` local-only.
- Rotate any key that is accidentally shared.
- Prefer local embeddings and local vector stores for sensitive memory.
