---
title: Alpha status & versioning
description: What "early alpha" means for RedScribe, current known limitations, and how versioning and releases work.
---

RedScribe is early alpha (`0.2.0-alpha.1` as of this writing). Expect rough
edges and breaking changes between releases, and read this page before
relying on it for a real client engagement.

## Known limitations

- **No public API.** Every workflow is web-UI-driven. There's no
  REST/GraphQL API to automate against yet.
- **The first-run `/setup/` page is a race, not an invite-only step.** It
  creates the instance's first Superadmin account and has no login of its
  own to gate it, by design, there's no admin yet to log in as. It works
  exactly once: the moment any Superadmin exists, it refuses to do
  anything further. In the window between an instance coming up and
  someone completing that form, whoever reaches it first becomes the
  Superadmin — normally the operator, moments after `docker compose up`,
  but on a network reachable by anyone else before that happens, it could
  be someone else instead. No engagement data exists yet at that point
  (nothing to disclose), and the CLI-only
  [`bootstrap_superadmin`](/reference/management-commands/#bootstrap_superadmin)
  command is the alternative if you'd rather not expose the web form at
  all on a network you don't fully trust yet. See [First
  run](/getting-started/first-run/) for both options.

## Versioning

RedScribe follows [Semantic Versioning](https://semver.org/):
`MAJOR.MINOR.PATCH`, with a `-alpha.N` / `-beta.N` / `-rc.N` pre-release
suffix before the first `1.0.0`. The current version lives in the repo's
`VERSION` file (a single line, no `v` prefix) and is tagged in git as
`v<version>` (for example `v0.1.0-alpha.1`).

Pre-1.0, **expect breaking changes on minor bumps** (`0.1.0` to `0.2.0`).
That's normal during alpha, not a mistake. Once RedScribe reaches `1.0.0`,
standard SemVer rules apply: `PATCH` for fixes, `MINOR` for
backward-compatible additions, `MAJOR` for breaking changes.

`CHANGELOG.md`, in the repo root, follows [Keep a
Changelog](https://keepachangelog.com/) format. Every release gets a dated
entry there before being tagged. See the [Changelog](/changelog/) page for
the current history.

## Cutting a release (maintainers)

```
# 1. Update VERSION and move [Unreleased] CHANGELOG entries into a new dated section.
# 2. Commit, then tag:
git tag -a v0.2.0-alpha.2 -m "v0.2.0-alpha.2"
git push origin v0.2.0-alpha.2
```
