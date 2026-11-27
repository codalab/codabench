# Security Policy

## Supported Versions

Security fixes are applied to the `develop` branch and included in the next release.
Only the [latest release](https://github.com/codalab/codabench/releases/latest) is supported.
If you run your own Codabench instance, please keep it up to date.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, pull requests, or discussions.**

Report them privately using one of the following channels:

- **GitHub:** go to the [Security tab](https://github.com/codalab/codabench/security) of this repository and click **Report a vulnerability**.
- **Email:** send the details to [info@codabench.org](mailto:info@codabench.org) with `[SECURITY]` in the subject line.

Please include as much of the following as possible:

- Type of issue (e.g. XSS, SQL injection, privilege escalation, sandbox escape in the compute worker)
- Affected component (Django app, API endpoint, frontend page, compute worker, etc.) and file paths if known
- Affected version, commit, or URL
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code, if available
- Impact of the issue and how an attacker might exploit it

## Handling of Reports

- We will investigate, keep you informed of our progress, and let you know when a fix is released.
- Please give us reasonable time to fix the issue before disclosing it publicly.
