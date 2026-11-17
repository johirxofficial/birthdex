# Security policy

## Supported versions

The latest release on the `main` branch is supported with security fixes.
Older tags may not receive patches.

| Version | Supported |
|---|---|
| 1.x | Yes |
| < 1.0 | No |

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Use GitHub's private reporting:

1. Open the repository's **Security** tab.
2. Choose **Advisories → Report a vulnerability**.

You can expect:

- An acknowledgement within a few days.
- A short assessment and, when confirmed, a fix and a coordinated disclosure
  date.
- Credit in the release notes if you want it.

## In scope

- Remote code execution, SQL/command injection, template injection.
- SSRF that reaches hosts other than the configured `PORTAL_BASE`.
- Cross-site scripting in the UI or API responses.
- Leaks of personal data through logs, responses, caches or error pages.
- Captcha session fixation, reuse, or cross-type confusion.
- Denial of service that is cheap for the attacker and not bounded by
  `CAPTCHA_CAPACITY` / `CAPTCHA_TTL`.

## Out of scope

- Reports that only say "the captcha can be solved by a human" — that is the
  product.
- Rate limits enforced by the upstream BDRIS portal.
- Vulnerabilities in the upstream portal itself (report those to BDRIS).
- Social engineering, spam or physical attacks.
- Missing security headers on a local development server.

## Handling of personal data

BirthDex deliberately stores nothing. When reporting, never include real
registration numbers, names, addresses or captcha answers. Use synthetic data.

## Deployment hardening

If you self-host a public instance, follow the checklist in
[docs/DEPLOY.md](docs/DEPLOY.md#8-security-checklist): HTTPS, `DEBUG=0`,
restricted `ALLOW_ORIGIN`, proxy-level rate limiting and a bounded
`CAPTCHA_CAPACITY`.
