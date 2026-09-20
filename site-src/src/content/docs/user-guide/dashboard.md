---
title: Dashboard & navigation
description: Orienting yourself in the RedScribe UI after logging in.
---

After login, `/` shows your dashboard, a personalized landing page rather
than a global one. What's on it depends on your role, but it generally
includes:

- Engagements you're a member of, or (with `engagements.view_all`) every
  active engagement.
- Findings currently assigned to you for review or QA, the same list that
  backs **My Queue** (`/reviews/`).
- Recent notifications.

## Sidebar

The sidebar is your primary navigation, organized around the objects
described in [Concepts & terminology](/start/concepts/):

| Section | Where it goes | Who sees it |
|---|---|---|
| Engagements | `/engagements/`, list, create, and open engagements | Everyone, scoped by membership unless `engagements.view_all` |
| Vulnerability Catalogue | `/catalogue/` | Everyone (contribute drafts); approve/manage needs `catalogue.*` |
| Checklist Templates | `/checklist-templates/` | Everyone (view); manage needs `checklist_templates.manage` |
| Report Profiles | `/report-profiles/` | Needs `report_settings.manage` |
| Trends | `/trends/` | Needs `reports.trends` |
| My Queue | `/reviews/` | Everyone with review/QA permissions |
| Notifications | `/notifications/` | Everyone |
| Search | `/search/` | Everyone, scoped to what you can already see |
| Clients | `/clients/` | Needs `clients.manage` |
| User Management | `/user-management/` | Needs `users.manage` |
| Role Management | `/roles/` | Needs `roles.manage` |
| Finding Structure | `/field-visibility/` | Needs `field_visibility.manage` |
| Feature Flags | `/feature-flags/` | Needs `feature_flags.manage` |
| Licensing | `/licensing/` | Needs `licensing.manage` |
| Audit Log | `/audit/` | Needs `audit_log.manage` |
| Branding | `/branding/` | Needs `branding.manage` |

See [Roles & permissions](/admin/roles-and-permissions/) for exactly what
each permission unlocks and which built-in role has it by default.

## Theme

A light/dark toggle sits in the sidebar and floats on auth screens too.
This is a per-browser preference, not an account setting.

## Notifications bell

The bell in the top bar shows unread in-app notifications: review/QA
assignments, review/QA outcomes, scope-change decisions, and new-account
setup links. See [Notifications & profile](/user-guide/notifications-and-profile/).
