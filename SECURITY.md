# Security Policy

## Supported versions

Only the latest `main` branch receives security fixes.

## Reporting a vulnerability

Email **Philopater.pentester@outlook.com** with reproduction steps and the
affected commit. Do not open a public issue for exploitable findings. Expect
an initial reply within 7 days.

## Scope

- In scope: the Streamlit control plane (`app/GUI/`), the agent core
  (`app/core/`, `app/tools/`), the installer (`scripts/ARGUS_INSTALLER.ps1`),
  and this repository's CI pipelines.
- Out of scope: the deliberately vulnerable benchmark fixtures (`benchmarks/`)
  and the containerized lab (`deploy/docker-lab/`) - they exist to be attacked.

## Deployment guidance

Defaults target an isolated lab (loopback-only, Kali in WSL2, `kali/kali`
bridge credentials in `.env.example`). Before any non-loopback deployment:
authenticate the control plane, keep `enableXsrfProtection = true`, and
replace the default bridge credentials. See
`docs/history/` (OWASP self-assessment summary) for the finding register.
