// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// Built output is written to ../docs (redscribe-docs/docs), so it can be
// committed and served straight from GitHub Pages ("Deploy from a branch",
// /docs folder on main) without a CI build step.
//
// Hosted as a GitHub *project* page (redscribe-labs.github.io/redscribe-docs/,
// not a custom domain or a user/org page at the repo root), so `base` and
// `site` are set accordingly below — every internal link and the sitemap
// depend on this being correct. If this ever moves to a custom domain or a
// redscribe-labs.github.io *user* page instead, drop `base` back to '/' and
// update `site` to match.
export default defineConfig({
	site: 'https://redscribe-labs.github.io/redscribe-docs/',
	base: '/redscribe-docs',
	outDir: '../docs',
	integrations: [
		starlight({
			title: 'RedScribe Docs',
			description:
				'Self-hosted engagement, finding, checklist, and report management for penetration testing teams.',
			favicon: '/favicon.svg',
			lastUpdated: false,
			pagination: true,
			customCss: ['./src/styles/custom.css'],
			sidebar: [
				{
					label: 'Start here',
					items: [
						{ label: 'What is RedScribe?', slug: 'index' },
						{ label: 'Alpha status & versioning', slug: 'start/alpha-status' },
						{ label: 'Concepts & terminology', slug: 'start/concepts' },
					],
				},
				{
					label: 'Getting Started',
					items: [
						{ label: 'Requirements & sizing', slug: 'getting-started/requirements' },
						{ label: 'Installation', slug: 'getting-started/installation' },
						{ label: 'First run', slug: 'getting-started/first-run' },
						{ label: 'Configuration reference', slug: 'getting-started/configuration' },
					],
				},
				{
					label: 'User Guide',
					items: [
						{ label: 'Logging in & MFA', slug: 'user-guide/login-and-mfa' },
						{ label: 'Dashboard & navigation', slug: 'user-guide/dashboard' },
						{ label: 'Engagements', slug: 'user-guide/engagements' },
						{ label: 'Findings', slug: 'user-guide/findings' },
						{ label: 'Vulnerability catalogue', slug: 'user-guide/catalogue' },
						{ label: 'Checklists', slug: 'user-guide/checklists' },
						{ label: 'Scanner import', slug: 'user-guide/scanner-import' },
						{ label: 'Reports & exports', slug: 'user-guide/reports' },
						{ label: 'Trends & search', slug: 'user-guide/trends-and-search' },
						{ label: 'Notifications & profile', slug: 'user-guide/notifications-and-profile' },
					],
				},
				{
					label: 'Client Portal',
					items: [
						{ label: 'For clients', slug: 'client-portal/for-clients' },
						{ label: 'Managing client access', slug: 'client-portal/managing-clients' },
					],
				},
				{
					label: 'Administration',
					items: [
						{ label: 'Roles & permissions', slug: 'admin/roles-and-permissions' },
						{ label: 'User management', slug: 'admin/user-management' },
						{ label: 'Finding structure', slug: 'admin/finding-structure' },
						{ label: 'Report profiles', slug: 'admin/report-profiles' },
						{ label: 'Feature flags', slug: 'admin/feature-flags' },
						{ label: 'Branding', slug: 'admin/branding' },
						{ label: 'Licensing', slug: 'admin/licensing' },
						{ label: 'Audit log', slug: 'admin/audit-log' },
						{ label: 'Backup & restore', slug: 'admin/backup-and-restore' },
					],
				},
				{
					label: 'Security',
					items: [
						{ label: 'Encryption model', slug: 'security/encryption' },
						{ label: 'Authentication & sessions', slug: 'security/authentication' },
						{ label: 'Audit trail & tamper evidence', slug: 'security/audit-trail' },
						{ label: 'Network & TLS', slug: 'security/network-and-tls' },
					],
				},
				{
					label: 'Deployment & Operations',
					items: [
						{ label: 'Docker Compose deep dive', slug: 'deployment/docker-compose' },
						{ label: 'Upgrading & rolling back', slug: 'deployment/upgrading' },
						{ label: 'Moving to a new machine', slug: 'deployment/moving-hosts' },
					],
				},
				{
					label: 'Developer Guide',
					items: [
						{ label: 'Architecture overview', slug: 'dev/architecture' },
						{ label: 'Local development', slug: 'dev/local-development' },
						{ label: 'Frontend asset builds', slug: 'dev/frontend-builds' },
						{ label: 'Testing', slug: 'dev/testing' },
						{ label: 'Contributing', slug: 'dev/contributing' },
						{ label: 'Report rendering pipeline', slug: 'dev/report-pipeline' },
						{ label: 'Scaling & concurrency model', slug: 'dev/scaling' },
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'Environment variables', slug: 'reference/environment-variables' },
						{ label: 'Management commands', slug: 'reference/management-commands' },
						{ label: 'Report template tags', slug: 'reference/report-template-tags' },
						{ label: 'DOCX template guide', slug: 'reference/docx-template-guide' },
						{ label: 'Checklist template format', slug: 'reference/checklist-template-format' },
						{ label: 'Data model & status reference', slug: 'reference/data-model' },
						{ label: 'Permissions reference', slug: 'reference/permissions' },
					],
				},
				{
					label: 'Changelog',
					items: [{ label: 'Changelog', slug: 'changelog' }],
				},
			],
		}),
	],
});
