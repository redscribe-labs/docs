---
title: Data model & status reference
description: Every status and severity enum in RedScribe, with its exact stored value and display label.
---

The authoritative list of every status and severity enum in the app, what
gets stored, and what label it shows as. Useful when reading a JSON export,
writing an integration, or just double-checking exact wording.

## Engagement

### `Engagement.status`

| Stored value | Label |
|---|---|
| `IN_PROGRESS` | In Progress |
| `IN_REVIEW` | In Review |
| `QA` | QA |
| `APPROVED` | Approved |
| `DELIVERED` | Delivered |
| `AWAITING_REMEDIATION_TEST` | Awaiting Remediation Test |
| `REMEDIATION_TEST` | Remediation Test |
| `CLOSED` | Closed |

Default: `IN_PROGRESS`. See [Engagements](/user-guide/engagements/#status-lifecycle)
for the transition order.

### `Engagement.test_type`

| Stored value | Label |
|---|---|
| `WEB_APPLICATION` | Web Application Penetration Test |
| `NETWORK` | Network Penetration Test |
| `VULNERABILITY_SCAN` | Vulnerability Scan |

Optional, blank by default.

### `ScopeChangeRequest.status`

| Stored value | Label |
|---|---|
| `PENDING` | Pending |
| `APPROVED` | Approved |
| `REJECTED` | Rejected |

Default: `PENDING`. See [Engagements](/user-guide/engagements/#scope-changes).

## Finding

### `Finding.severity`

| Stored value | Label |
|---|---|
| `CRITICAL` | Critical |
| `HIGH` | High |
| `MEDIUM` | Medium |
| `LOW` | Low |
| `INFORMATIONAL` | Informational |

No default, it's required at creation.

### `Finding.status`

| Stored value | Label |
|---|---|
| `OPEN` | Open |
| `CLOSED` | Closed |

Default: `OPEN`. This tracks whether the underlying vulnerability is
currently present, independent of `workflow_status` below.

### `Finding.workflow_status`

| Stored value | Label |
|---|---|
| `DRAFT` | Draft |
| `REVIEWED` | Reviewed |
| `REVIEW_CHANGES_REQUESTED` | Changes Requested (Review) |
| `QA_APPROVED` | QA Approved |
| `QA_CHANGES_REQUESTED` | Changes Requested (QA) |

Default: `DRAFT`. See [Findings](/user-guide/findings/#the-review-workflow)
for the full transition diagram.

### `Finding.retest_status`

| Stored value | Label |
|---|---|
| `NOT_RETESTED` | Not Retested |
| `FIXED` | Fixed |
| `NOT_FIXED` | Not Fixed |
| `PARTIALLY_FIXED` | Partially Fixed |
| `RISK_ACCEPTED` | Risk Accepted |

Default: `NOT_RETESTED`. See [Findings](/user-guide/findings/#retesting).

`Finding.source_template` links a finding to the catalogue entry it was
started from, if any. It's a record of origin only: editing or deleting the
entry doesn't change the finding (deleting it clears the link).

## Vulnerability catalogue

### `VulnerabilityTemplate.status`

| Stored value | Label |
|---|---|
| `DRAFT` | Draft |
| `PENDING_QA` | Pending QA |
| `APPROVED` | Approved |

Default: `DRAFT`. See [Vulnerability catalogue](/user-guide/catalogue/#the-workflow).

## Checklist

### `ChecklistItem.status`

| Stored value | Label |
|---|---|
| `NOT_TESTED` | Not Tested |
| `TESTED_NO_FINDING` | Tested — No Finding |
| `TESTED_FINDING_RAISED` | Tested — Finding Raised |
| `NOT_APPLICABLE` | Not Applicable |
| `BLOCKED` | Blocked |

Default: `NOT_TESTED`. `BLOCKED` requires a reason. See
[Checklists](/user-guide/checklists/#the-testing-posture-page).

### `ChecklistItemEvent.kind`

One row per change to a checklist item, shown as its Activity list.
Encrypted fields are recorded as "changed" without their content.

| Stored value | Recorded when |
|---|---|
| `STATUS` | The outcome changes (old and new labels stored) |
| `ASSIGNEE` | The assignee changes (old and new names stored) |
| `EVIDENCE` | Test results and evidence are edited |
| `SCOPE` | *What was tested* is edited |
| `FINDINGS` | Linked findings change (old and new counts stored) |
| `COMMENT` | A comment is added |

## Accounts

### `User.auth_type`

| Stored value | Label |
|---|---|
| `LOCAL` | Local username/password |
| `OAUTH` | OAuth |

Default: `LOCAL`. See [Configuration](/getting-started/configuration/#authentication).

### Built-in role slugs

Not a `TextChoices` enum, since roles are dynamic database rows (see [Roles &
permissions](/admin/roles-and-permissions/)), but four slugs are
special-cased in code as the built-in starting roles: `SUPERADMIN`,
`TEAM_LEAD`, `SENIOR`, `CONSULTANT`.
