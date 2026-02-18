# Security Policy for Square Tools

This repository handles Square API access, local catalog cache operations, and image processing workflows.

## 1. Secrets Handling

- Preferred token variable: `SQUARE_ACCESS_TOKEN`
- Legacy fallback variable: `SQUARE_TOKEN`
- Additional sensitive vars: `REMOVEBG_API_KEY`, `GEMINI_API_KEY`, `BANANA_API_KEY`
- Never commit real credentials to tracked files.
- Use placeholders such as `your_key_here` in docs and examples.

## 2. Key Rotation

If a key appears in git-tracked content:

1. Rotate/revoke the key in the provider dashboard immediately.
2. Replace committed value with placeholder text.
3. Record incident details and rotation timestamp in your operational log.
4. Re-run secret scanning before merge.

## 3. Runtime Safety Controls

- Runtime policy lives under `runtime/`.
- Preflight checks are enforced via `bin/agent_preflight.sh`.
- Privileged operations (`Photos`, `JS injection`, cache mutations) must be blocked when mode/capability requirements are not met.

## 4. Logging and Redaction

- Do not print raw tokens in normal command output.
- Redact secrets in debug output (`prefix...`).
- Avoid persisting secret-bearing payloads in logs or markdown docs.

## 5. Secret Scanning Gate

Run before commit/release:

```bash
./bin/secret_scan.sh
```

A non-zero exit means potential secrets were detected and must be fixed first.
