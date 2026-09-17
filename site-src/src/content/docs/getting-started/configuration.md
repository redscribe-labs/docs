---
title: Configuration
description: How RedScribe is configured, and where to find every setting.
---

All configuration is via environment variables, normally set in `.env`
(copied from `.env.example`, see [Installation](/getting-started/installation/)).
Settings are cross-referenced against `config/settings/base.py` /
`config/settings/prod.py` where `.env.example`'s own comments don't spell out
the default or behavior.

The full, authoritative table of every variable, its purpose and default,
lives on the [Environment variables](/reference/environment-variables/)
reference page. This page covers the handful of settings areas worth
understanding conceptually before you tune them.

## Dev vs. prod settings

`DJANGO_SETTINGS_MODULE` picks between two settings modules:

- **`config.settings.dev`**, the `.env.example` default. It has no
  HTTPS-redirect behavior, so it works whether or not anything is
  terminating TLS in front of it. Used by [Installation Method
  3](/getting-started/installation/#method-3-docker-compose-plain-http).
- **`config.settings.prod`**, for real deployment behind a TLS-terminating
  reverse proxy ([Methods 1 and 2](/getting-started/installation/)). It sets
  `SECURE_PROXY_SSL_HEADER` to trust `X-Forwarded-Proto: https` from that
  proxy, and hard-enforces HTTPS/HSTS/secure cookies once that's set.

<details>
<summary>Common mistake: redirect loops</summary>

Don't point `prod.py` at port 8000 directly without a proxy in front setting
the `X-Forwarded-Proto` header. Doing so force-redirects everything to
HTTPS and you'll get a redirect loop.

</details>

## Authentication

Local username/password is always available. OAuth (Google or Microsoft) can
be layered on via `OAUTH_PROVIDER`. RedScribe is single-tenant per instance,
so OAuth sign-in is locked to exactly one provider and one email domain
(`OAUTH_ALLOWED_DOMAIN`); anyone authenticating with a valid provider account
outside that domain is rejected before an account is created. See
[Authentication & sessions](/security/authentication/) for the full model,
including MFA, lockout, and session policy.

## Email

Password-reset links and change notifications go out via SMTP
(`EMAIL_HOST` and friends). Leave `EMAIL_HOST` blank during evaluation to use
Django's console backend, so emails are printed to the app log instead of
sent. That's fine for local or dev use, but not for production.

## Encryption, audit, and backup settings

These three areas each have their own dedicated docs page, since the
*settings* only make sense alongside how the feature actually behaves:

- [Encryption model](/security/encryption/), covering `REDSCRIBE_ROOT_KEY`.
- [Audit log](/admin/audit-log/), covering `AUDIT_LOG_RETENTION_DAYS`.
- [Backup & restore](/admin/backup-and-restore/), covering `BACKUP_DIR`,
  `BACKUP_ENCRYPTION_PASSPHRASE`, and `BACKUP_RETENTION_DAYS`.
