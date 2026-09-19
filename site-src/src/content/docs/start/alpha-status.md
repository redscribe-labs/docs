---
title: Alpha status & versioning
description: What "early alpha" means for RedScribe, current known limitations, and how versioning and releases work.
---

RedScribe is early alpha (`0.1.0-alpha.1` as of this writing), so expect
rough edges and breaking changes between releases. Read this page before
relying on it for a real client engagement.

## Known limitations

- **No public API.** Every workflow is web-UI-driven; there is no REST/GraphQL
  API to automate against yet.

## Versioning

RedScribe follows [Semantic Versioning](https://semver.org/), using
`MAJOR.MINOR.PATCH` with a `-alpha.N` / `-beta.N` / `-rc.N` pre-release
suffix before the first `1.0.0`. The current version lives in the repo's
`VERSION` file (single line, no `v` prefix) and is tagged in git as
`v<version>` (e.g. `v0.1.0-alpha.1`).

**Pre-1.0, expect breaking changes on minor bumps** (`0.1.0` to `0.2.0`).
That's normal during alpha, not a mistake. Once RedScribe reaches `1.0.0`,
standard SemVer compatibility rules apply: `PATCH` for fixes, `MINOR` for
backward-compatible additions, `MAJOR` for breaking changes.

`CHANGELOG.md` (in the repo root) follows [Keep a
Changelog](https://keepachangelog.com/) format, and every release gets a
dated entry there before being tagged. See the [Changelog](/changelog/) page
for the current history.

## Cutting a release (maintainers)

```
# 1. Update VERSION and move [Unreleased] CHANGELOG entries into a new dated section.
# 2. Commit, then tag:
git tag -a v0.1.0-alpha.2 -m "v0.1.0-alpha.2"
git push origin v0.1.0-alpha.2
```
