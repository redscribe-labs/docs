---
title: Configuration
description: How RedScribe is configured, and where to find every setting.
---

Everything about how RedScribe runs is set through environment variables,
usually in your `.env` file (copied from `.env.example` during
[installation](/getting-started/installation/)). This page walks through
the handful of settings worth understanding conceptually before you tune
them. For the full list of every variable, its purpose, and its default,
see the [Environment variables](/reference/environment-variables/)
reference page.

## Development vs. production settings

One setting, `DJANGO_SETTINGS_MODULE`, decides which of two modes
RedScribe runs in:

- **Development mode**, the default out of the box. It doesn't redirect
  anything to HTTPS, so it works whether or not something in front of it
  is handling TLS. This is what [Installation Method
  3](/getting-started/installation/#method-3-docker-compose-plain-http)
  uses.
- **Production mode**, for a real deployment sitting behind a TLS
  terminating reverse proxy
  ([Methods 1 and 2](/getting-started/installation/)). It trusts that
  proxy's signal that the original request was HTTPS, and once that's
  set, it enforces HTTPS, strict transport security, and secure cookies
  across the board.

<details>
<summary>Common mistake: redirect loops</summary>

Don't point production mode at the app directly, without a proxy in front
of it signaling that the request came in over HTTPS. Doing that forces
every request into an HTTPS redirect it can never satisfy, and you end up
with a redirect loop.

</details>

## Authentication

A local username and password always works. You can layer OAuth (Google
or Microsoft) on top of that. Since one RedScribe instance serves one
organization, OAuth sign in is locked to exactly one provider and one
email domain: anyone who authenticates successfully but falls outside
that domain is rejected before an account is even created. See
[Authentication & sessions](/security/authentication/) for the full
picture, including multi factor authentication, lockout, and session
behavior.

## Email

Password reset links and change notifications go out over SMTP. Leave the
mail server setting blank while you're evaluating RedScribe, and emails
print to the app's log instead of actually sending, which is fine for
local or development use, but not for anything real.

## Encryption, audit, and backup settings

These three areas each get their own dedicated page, since the settings
only make sense alongside how the feature actually behaves:

- [Encryption model](/security/encryption/), covering the instance's root
  key.
- [Audit log](/admin/audit-log/), covering how long audit history is kept.
- [Backup & restore](/admin/backup-and-restore/), covering where backups
  are stored, how they're encrypted, and how long they're kept.
