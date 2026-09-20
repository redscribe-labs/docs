"""
Seeds the "Umbrella Corporation" sample engagement shown in the docs at
https://docs.redscribe.app/user-guide/sample-report/ -- the same Report
Profile, Finding Structure, and 10 findings that produced the sample PDF
linked from that page. Exporting a PDF from the seeded engagement (with a
freshly-generated Report Profile default, or overriding cover title /
classification label to "SAMPLE Web Application Penetration Test Report"
/ "AI GENERATED REPORT CONTENT" on the report's Configure page) reproduces
that sample.

Run this against a disposable/demo instance, not production -- it creates
real Client/Engagement/Finding/ReportProfile/User rows. It is safe to
re-run: existing rows are looked up by their natural key (profile name,
client name, engagement reference number, content-section slug, username)
and updated in place rather than duplicated.

    docker compose exec -T web python manage.py shell < seed-sample-report.py

(-T disables the pseudo-TTY, needed for piped stdin under Compose.)

New demo accounts are created with the placeholder password below --
change it, and the emails, before running this against anything other
than a fully disposable instance.
"""

import json

from django.utils import timezone

from apps.accounts.models import Role, User
from apps.clients.models import Client
from apps.crypto.services import encrypt_bytes, generate_project_key, get_data_key, record_aad
from apps.engagements.models import Engagement, EngagementMembership, EngagementStatusHistory
from apps.findings.models import ClassificationTag, ContentSectionDefinition, Finding, FindingSection
from apps.reports.models import ReportConfig, ReportProfile, ReportTextBlockDefinition

DEMO_PASSWORD = "ChangeMe123!"  # noqa -- disposable-instance-only demo accounts, see module docstring


# ------------------------------------------------------------------ finding structure

CONTENT_SECTIONS = [   {   'slug': 'vulnerability-description',
        'label': 'Description',
        'order': 10,
        'is_active': True,
        'supports_image_upload': False,
        'portal_visible': True,
        'include_in_remediation_report_only': False,
        'is_import_target': True,
        'is_protected': False},
    {   'slug': 'business-technical-impact',
        'label': 'Impact',
        'order': 20,
        'is_active': True,
        'supports_image_upload': False,
        'portal_visible': True,
        'include_in_remediation_report_only': False,
        'is_import_target': True,
        'is_protected': False},
    {   'slug': 'affects',
        'label': 'Affected Assets',
        'order': 30,
        'is_active': True,
        'supports_image_upload': False,
        'portal_visible': False,
        'include_in_remediation_report_only': False,
        'is_import_target': False,
        'is_protected': True},
    {   'slug': 'proof-of-concept',
        'label': 'Evidence',
        'order': 40,
        'is_active': True,
        'supports_image_upload': False,
        'portal_visible': True,
        'include_in_remediation_report_only': False,
        'is_import_target': True,
        'is_protected': False},
    {   'slug': 'remediations',
        'label': 'Remediations',
        'order': 50,
        'is_active': True,
        'supports_image_upload': False,
        'portal_visible': True,
        'include_in_remediation_report_only': False,
        'is_import_target': True,
        'is_protected': False},
    {   'slug': 'references',
        'label': 'References',
        'order': 60,
        'is_active': True,
        'supports_image_upload': False,
        'portal_visible': True,
        'include_in_remediation_report_only': False,
        'is_import_target': True,
        'is_protected': False}]

for section in CONTENT_SECTIONS:
    ContentSectionDefinition.objects.get_or_create(
        slug=section["slug"],
        defaults={
            "label": section["label"],
            "order": section["order"],
            "is_active": section["is_active"],
            "supports_image_upload": section["supports_image_upload"],
            "portal_visible": section["portal_visible"],
            "include_in_remediation_report_only": section["include_in_remediation_report_only"],
            "is_import_target": section["is_import_target"],
            "is_protected": section["is_protected"],
        },
    )
print(f"Content sections: {ContentSectionDefinition.objects.count()} total")


# ------------------------------------------------------------------ report profile

PROFILE_TEMPLATE = {   'type': 'doc',
    'content': [   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ cover_page }}', 'type': 'text'}]},
                   {'type': 'pageBreak'},
                   {   'type': 'paragraph',
                       'attrs': {'lead': True},
                       'content': [{'text': 'Document Control', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ document_control }}', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': True},
                       'content': [{'text': 'Engagement timeline', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ engagement_lifecycle }}', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ table_of_contents }}', 'type': 'text'}]},
                   {'type': 'pageBreak'},
                   {   'type': 'heading',
                       'attrs': {'level': 1},
                       'content': [{'text': 'Executive Summary', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ executive_summary }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Assessment Overview', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ assessment_overview }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Overall Security Posture', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ overall_security_posture }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Breakdown of Findings', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ breakdown_of_findings }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 1},
                       'content': [{'text': 'Findings', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ finding_details }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 1},
                       'content': [{'text': 'Observations', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ observations }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 1},
                       'content': [{'text': 'Scope and Constraints', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Scope of Testing', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ scope }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Testing Conditions', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ testing_conditions }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Assessment Team', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ assessment_team }}', 'type': 'text'}]},
                   {'type': 'pageBreak'},
                   {   'type': 'heading',
                       'attrs': {'level': 1},
                       'content': [{'text': 'Assessment Methodology', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ testing_methodology }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Testing Phases', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ testing_phases }}', 'type': 'text'}]},
                   {   'type': 'heading',
                       'attrs': {'level': 2},
                       'content': [{'text': 'Severity Scoring Guide', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ scoring_guide }}', 'type': 'text'}]},
                   {'type': 'pageBreak'},
                   {   'type': 'heading',
                       'attrs': {'level': 1},
                       'content': [{'text': 'Confidentiality & Disclaimer', 'type': 'text'}]},
                   {   'type': 'paragraph',
                       'attrs': {'lead': False},
                       'content': [{'text': '{{ confidentiality_disclaimer }}', 'type': 'text'}]}]}

PROFILE_APPEARANCE = {   'cover_title': 'Penetration Test Report',
    'classification_label': 'Strictly Confidential',
    'finding_id_prefix': 'F',
    'severity_colors': {   'LOW': {'open': '', 'closed': ''},
                           'HIGH': {'open': '', 'closed': ''},
                           'MEDIUM': {'open': '', 'closed': ''},
                           'CRITICAL': {'open': '', 'closed': ''},
                           'INFORMATIONAL': {'open': '', 'closed': ''}},
    'body_font': 'Plus Jakarta Sans',
    'monospace_font': 'JetBrains Mono',
    'bullet_character': '•',
    'table_header_color': 'rgb(42,42,42)',
    'empty_cell_background_color': 'rgba(237,238,238,1)',
    'finding_table_layout': 'table',
    'labels': {}}

profile, _created = ReportProfile.objects.get_or_create(
    name='Web Application',
    defaults={"template": PROFILE_TEMPLATE, **PROFILE_APPEARANCE},
)
profile.template = PROFILE_TEMPLATE
for field, value in PROFILE_APPEARANCE.items():
    setattr(profile, field, value)
profile.save()

TEXT_BLOCKS = [   ('assessment_overview', 'Assessment Overview'),
    ('confidentiality_disclaimer', 'Confidentiality Disclaimer'),
    ('engagement_lifecycle', 'Engagement Lifecycle'),
    ('executive_summary', 'Executive Summary'),
    ('overall_security_posture', 'Overall Security Posture'),
    ('scoring_guide', 'Scoring Guide'),
    ('testing_conditions', 'Testing Conditions'),
    ('testing_methodology', 'Testing Methodology')]

for slug, label in TEXT_BLOCKS:
    ReportTextBlockDefinition.objects.get_or_create(profile=profile, slug=slug, defaults={"label": label})

# block_defaults values are stored double-encoded (each value is itself a
# JSON string of a Tiptap doc), matching what's already on disk for this
# profile -- see admin/report-profiles.mdx#text-blocks.
BLOCK_DEFAULTS = {   'assessment_overview': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                           'primary objective was to evaluate the security posture of the target '
                           'application, identify technical vulnerabilities capable of '
                           'exploitation by unauthorized actors, and establish clear remediation '
                           'steps. Testing evaluated key security mechanisms across the scope '
                           'specified in {{ scope }}, focusing on authentication controls, session '
                           'management, input validation, and access controls between the '
                           'Consultant, Senior Consultant, and Team Lead roles, while '
                           'administrative functions under the Admin role remained strictly out of '
                           'scope."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                           'engagement utilized a hybrid testing methodology combining automated '
                           'vulnerability analysis with manual exploitation techniques to minimize '
                           'false positives and uncover complex logic flaws. All activities were '
                           'executed to ensure continuous operational stability of the target '
                           'environment while rigorously testing application defenses against '
                           'established security standards. Full details regarding specific '
                           'technical findings, security observations, and tactical remediation '
                           'recommendations are detailed within the subsequent sections of this '
                           'report generated on {{ report_date }}."}]}]}',
    'confidentiality_disclaimer': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"This '
                                  'report contains confidential and proprietary security '
                                  'information belonging to {{ client_name }}. The contents of '
                                  'this document, including all technical findings, application '
                                  'architecture details, and vulnerability data, are intended '
                                  'solely for the internal use of {{ client_name }} under '
                                  'engagement reference {{ reference_number }}. Unauthorized '
                                  'distribution, reproduction, or dissemination of this material, '
                                  'in whole or in part, without the prior written consent of {{ '
                                  'client_name }} is strictly '
                                  'prohibited."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                                  'assessment activities performed between {{ start_date }} and {{ '
                                  'end_date }} by {{ prepared_by }} represent a point in time '
                                  'evaluation of the security posture of the target application '
                                  'specified within {{ scope }}. While industry recognised '
                                  'security testing standards and manual verification techniques '
                                  'were utilized, no security assessment can guarantee the '
                                  'complete identification of all potential vulnerabilities or '
                                  'technical flaws. The author accepts no liability for '
                                  'operational disruptions, security incidents, or financial '
                                  'losses arising from the reliance on this report, or from '
                                  'unmitigated vulnerabilities present within the target '
                                  'environment following the generation of this document on {{ '
                                  'report_date }}."}]}]}',
    'engagement_lifecycle': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                            'penetration testing engagement for {{ client_name }} under reference '
                            '{{ reference_number }} follows a formal life cycle designed to ensure '
                            'thorough technical evaluation, clear communication, and structured '
                            'remediation support. Initiated on {{ start_date }}, the engagement '
                            'progressed through preliminary scoping, active technical testing, '
                            'finding verification, and reporting, concluding on {{ end_date }} '
                            'with the delivery of this formal deliverable prepared by {{ '
                            'prepared_by '
                            '}}."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Following '
                            'the presentation of this report on {{ report_date }}, the engagement '
                            'transitions into the remediation phase. {{ client_name }} may utilize '
                            'the detailed technical findings and recommendations contained herein '
                            'to address identified security gaps. A formal retesting window may be '
                            'scheduled upon request to validate the effectiveness of implemented '
                            'fixes and update the overall risk posture '
                            'accordingly."}]},{"type":"table","content":[{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Phase"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Description"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Date '
                            '/ '
                            'Status"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Scoping '
                            'and '
                            'Authorization"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Definition '
                            'of target assets, rules of engagement, and role access '
                            'parameters"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"{{ '
                            'start_date '
                            '}}"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Active '
                            'Technical '
                            'Testing"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Execution '
                            'of automated scanning and manual exploitation across target '
                            'scope"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"In '
                            'Progress / '
                            'Complete"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Draft '
                            'Reporting"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Compilation '
                            'of findings, risk scoring, and evidence verification by {{ '
                            'prepared_by '
                            '}}"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"{{ '
                            'end_date '
                            '}}"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Deliverable '
                            'Presentation"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Final '
                            'report delivery and executive briefing provided on {{ report_date '
                            '}}"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Complete"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Remediation '
                            'and '
                            'Retesting"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Validation '
                            'of implemented client fixes and updated risk '
                            'assessment"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Pending"}]}]}]}]},{"type":"paragraph","attrs":{"lead":false}},{"type":"paragraph","attrs":{"lead":false}}]}',
    'executive_summary': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                         'the assessment period from {{ start_date }} to {{ end_date }}, {{ '
                         'prepared_by }} conducted a comprehensive web application penetration '
                         'test against {{ scope }} for {{ client_name }} under engagement '
                         'reference {{ reference_number }}. The evaluation aimed to determine the '
                         'resilience of the application against unauthorized access, privilege '
                         'escalation, and data exposure across the Consultant, Senior Consultant, '
                         'and Team Lead operational roles, while administrative platform functions '
                         'remained out of '
                         'scope."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Testing '
                         'identified several key areas requiring immediate technical remediation '
                         'to strengthen application defenses. The detailed technical findings and '
                         'security observations compiled in this deliverable on {{ report_date }} '
                         'provide {{ client_name }} with the necessary guidance to address '
                         'identified vulnerabilities, lower overall risk, and prevent potential '
                         'security compromises in production systems."}]}]}',
    'overall_security_posture': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                                'target application demonstrates baseline security controls across '
                                'standard authentication workflows; however, critical gaps in '
                                'authorization enforcement and session management were identified. '
                                'These weaknesses could allow lower-privileged users, such as '
                                'those in the Consultant role, to bypass functional boundaries and '
                                'perform unauthorized actions reserved for Senior Consultant or '
                                'Team Lead '
                                'accounts."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                                'security posture reflects an environment with adequate parameter '
                                'input sanitization but insufficient defense in depth regarding '
                                'multi-tenant isolation and access control checks at the API '
                                'layer. Addressing these systemic vulnerabilities is essential to '
                                'ensure that application logic consistently enforces business '
                                'rules across all operational roles before the system is exposed '
                                'to wider operational risks."}]}]}',
    'scoring_guide': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Vulnerability '
                     'severity is calculated using the Common Vulnerability Scoring System (CVSS) '
                     'v4.0 specification, evaluating macro vector metrics including attack vector, '
                     'complexity, attack requirements, privileges required, user interaction, and '
                     'subsequent impact on confidentiality, integrity, and availability across '
                     'both vulnerable and subsequent systems. Severity ratings assist {{ '
                     'client_name }} in prioritizing remediation efforts effectively according to '
                     'risk '
                     'exposure."}]},{"type":"table","content":[{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Risk '
                     'Level"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"CVSS '
                     'v4.0 Score '
                     'Range"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Operational '
                     'Definition"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Suggested '
                     'Remediation '
                     'Window"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Critical"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"9.0 '
                     '– '
                     '10.0"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Exploitation '
                     'requires minimal effort or prerequisites and leads to complete compromise of '
                     'systems, critical data, or multi tenant '
                     'boundaries."}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Immediate '
                     'emergency patch (24–48 '
                     'hours)"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"High"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"7.0 '
                     '– '
                     '8.9"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Exploitation '
                     'can result in significant privilege escalation, unauthorized system access, '
                     'or major data '
                     'exposure."}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"High '
                     'priority resolution (7–14 '
                     'days)"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Medium"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"4.0 '
                     '– '
                     '6.9"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Exploitation '
                     'requires specific conditions or existing access privileges, resulting in '
                     'localized component impact or moderate data '
                     'disclosure."}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Scheduled '
                     'sprint release (30 '
                     'days)"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Low"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"0.1 '
                     '– '
                     '3.9"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Minor '
                     'technical issues, security misconfigurations, or minor information leaks '
                     'with low operational '
                     'impact."}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"General '
                     'maintenance cycle (60–90 '
                     'days)"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Informational"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"0.0"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Security '
                     'hygiene observations, defense in depth recommendations, or best practice '
                     'improvements with no direct impact '
                     'score."}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Operational '
                     'review at discretion"}]}]}]}]},{"type":"paragraph","attrs":{"lead":false}}]}',
    'testing_conditions': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Testing '
                          'activities were conducted remotely using automated vulnerability '
                          'scanners and manual security analysis tools, with traffic originating '
                          'from designated assessor IP addresses to prevent interference with '
                          'production operations. Assessors evaluated application controls across '
                          'defined functional roles, including Consultant, Senior Consultant, and '
                          'Team Lead, while administrative vendor functions under the Admin role '
                          'remained strictly out of '
                          'scope."}]},{"type":"paragraph","attrs":{"lead":false}},{"type":"table","content":[{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":[204],"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Assessment '
                          'Parameter"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Operational '
                          'Condition"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":[204],"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Environment '
                          'Type"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Dedicated '
                          'staging '
                          'environment"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":[204],"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Originating '
                          'IP '
                          'Addresses"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Designated '
                          'assessor proxy addresses provided to {{ client_name '
                          '}}"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":[204],"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Testing '
                          'Approaches"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Hybrid '
                          'model incorporating automated scanning and manual logic '
                          'exploitation"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":[204],"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"User '
                          'Role '
                          'Matrix"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"In '
                          'scope: Consultant, Senior Consultant, Team Lead. Out of scope: '
                          'Admin"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":[204],"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Active '
                          'Constraints"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Rate '
                          'limits relaxed for testing duration; web application firewall placed in '
                          'logging mode"}]}]}]}]},{"type":"paragraph","attrs":{"lead":false}}]}',
    'testing_methodology': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                           'evaluation combines structural reconnaissance, automated scanning, '
                           'manual vulnerability identification, and controlled exploitation to '
                           'validate security controls. Special emphasis was placed on access '
                           'control enforcement across the Consultant, Senior Consultant, and Team '
                           'Lead roles, ensuring that data isolation and role permissions are '
                           'strictly maintained at the server '
                           'level."}]},{"type":"table","content":[{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Methodology '
                           'Phase"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Core '
                           'Objective"}]}]},{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Key '
                           'Activities"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Information '
                           'Gathering"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Map '
                           'target attack surface and application '
                           'architecture"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Endpoint '
                           'enumeration, role workflow identification, and technological stack '
                           'profiling"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Threat '
                           'Modeling"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Identify '
                           'high risk entry points and logic '
                           'boundaries"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Mapping '
                           'authorization boundaries between Consultant, Senior Consultant, and '
                           'Team Lead '
                           'roles"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Vulnerability '
                           'Analysis"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Discover '
                           'potential security weaknesses and '
                           'misconfigurations"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Automated '
                           'security scanning and deep manual analysis of input '
                           'parameters"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Exploitation '
                           '& '
                           'Verification"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Confirm '
                           'vulnerability exploitability and determine '
                           'impact"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Controlled '
                           'manual exploitation to validate data leakage and privilege escalation '
                           'paths"}]}]}]},{"type":"tableRow","content":[{"type":"tableHeader","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Reporting '
                           '& '
                           'Guidance"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Compile '
                           'technical findings and remediation '
                           'steps"}]}]},{"type":"tableCell","attrs":{"colspan":1,"rowspan":1,"colwidth":null,"align":null},"content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Risk '
                           'scoring using CVSS v4.0 metrics and formulating actionable fix '
                           'guidance"}]}]}]}]},{"type":"paragraph","attrs":{"lead":false}}]}'}
profile.block_defaults = BLOCK_DEFAULTS
profile.save(update_fields=["block_defaults"])
print(f"Report profile: {profile.name!r} ({len(TEXT_BLOCKS)} text blocks)")


# ------------------------------------------------------------------ client + engagement

client, _created = Client.objects.get_or_create(name="Umbrella Corporation")

engagement, created = Engagement.objects.get_or_create(
    reference_number="RS-UMB-0369",
    defaults={
        "client": client,
        "client_name": client.name,
        "scope": 'https://redscribe.app',
        "start_date": '2026-09-12',
        "end_date": '2026-09-25',
        "status": Engagement.Status.APPROVED,
    },
)
if not created:
    engagement.client = client
    engagement.scope = 'https://redscribe.app'
    engagement.start_date = '2026-09-12'
    engagement.end_date = '2026-09-25'
    engagement.status = Engagement.Status.APPROVED
    engagement.save()

# A ProjectKey is required before any encrypted finding content can be
# written -- see security/encryption.mdx.
try:
    data_key = get_data_key(engagement)
except Exception:
    generate_project_key(engagement)
    data_key = get_data_key(engagement)
print(f"Engagement: {engagement.client_name} ({engagement.reference_number})")


# ------------------------------------------------------------------ assessment team

TEAM = [   {   'username': 'mblake',
        'first_name': 'Morgan',
        'last_name': 'Blake',
        'email': 'morgan.blake@example.com',
        'role': 'Team Lead',
        'qualifications': '{"type": "doc", "content": [{"type": "bulletList", "content": [{"type": '
                          '"listItem", "content": [{"type": "paragraph", "content": [{"type": '
                          '"text", "text": "PMP (Project Management Professional)"}]}]}, {"type": '
                          '"listItem", "content": [{"type": "paragraph", "content": [{"type": '
                          '"text", "text": "CISM (Certified Information Security Manager)"}]}]}, '
                          '{"type": "listItem", "content": [{"type": "paragraph", "content": '
                          '[{"type": "text", "text": "B.Sc. in Computer Science & Information '
                          'Systems"}]}]}]}]}',
        'background': '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": '
                      '"text", "text": "Morgan has 12+ years of experience leading '
                      'cross-functional cyber security consulting teams. Within the application, '
                      'Morgan holds full administrative authority over the workspace, including '
                      'the ability to approve high-value client deliverables, manage team billing, '
                      'adjust workspace permissions, and assign engagement leads."}]}]}'},
    {   'username': 'rchen',
        'first_name': 'Robin',
        'last_name': 'Chen',
        'email': 'robin.chen@example.com',
        'role': 'Senior Consultant',
        'qualifications': '{"type": "doc", "content": [{"type": "bulletList", "content": [{"type": '
                          '"listItem", "content": [{"type": "paragraph", "content": [{"type": '
                          '"text", "text": "OSCP (Offensive Security Certified '
                          'Professional)"}]}]}, {"type": "listItem", "content": [{"type": '
                          '"paragraph", "content": [{"type": "text", "text": "CISSP (Certified '
                          'Information Systems Security Professional)"}]}]}, {"type": "listItem", '
                          '"content": [{"type": "paragraph", "content": [{"type": "text", "text": '
                          '"M.Sc. in Cybersecurity & Threat Intelligence"}]}]}]}]}',
        'background': '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": '
                      '"text", "text": "Robin is a lead technical assessor with 6 years of '
                      'penetration testing and cloud security evaluation experience. In the '
                      'application, Robin has elevated operational privileges and capable of '
                      'conducting technical assessments, generating client draft reports, '
                      'modifying scope parameters, and peer-reviewing work produced by junior team '
                      'members."}]}]}'},
    {   'username': 'treed',
        'first_name': 'Taylor',
        'last_name': 'Reed',
        'email': 'taylor.reed@example.com',
        'role': 'Consultant',
        'qualifications': '{"type": "doc", "content": [{"type": "bulletList", "content": [{"type": '
                          '"listItem", "content": [{"type": "paragraph", "content": [{"type": '
                          '"text", "text": "CEH (Certified Ethical Hacker)"}]}]}, {"type": '
                          '"listItem", "content": [{"type": "paragraph", "content": [{"type": '
                          '"text", "text": "CompTIA Security+"}]}]}, {"type": "listItem", '
                          '"content": [{"type": "paragraph", "content": [{"type": "text", "text": '
                          '"B.Sc. in Cybersecurity"}]}]}]}]}',
        'background': '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": '
                      '"text", "text": "Taylor joined the firm 18 months ago and focuses on '
                      'vulnerability scanning, baseline web application testing, and initial '
                      'evidence gathering. Taylor\\u2019s application permissions are strictly '
                      'restricted to standard operations: creating draft finding logs, uploading '
                      'raw testing evidence, and viewing only explicitly assigned engagement '
                      'workspace."}]}]}'}]

team_users = {}
for member in TEAM:
    # get_or_create with no `permissions` creates a brand-new role with zero
    # permissions if one by this name doesn't already exist on this instance
    # (built-in "Team Lead"/"Consultant" from setup, or a custom "Senior
    # Consultant" role, both get reused as-is if present). Assign real
    # permissions from Roles & Permissions afterward if these demo accounts
    # need to actually log in and do something, not just show up in the
    # report's Assessment Team section.
    role, _created = Role.objects.get_or_create(
        name=member["role"], defaults={"slug": member["role"].lower().replace(" ", "-")},
    )
    user, created = User.objects.get_or_create(
        username=member["username"],
        defaults={
            "email": member["email"], "first_name": member["first_name"], "last_name": member["last_name"],
            "role": role, "qualifications": member["qualifications"], "background": member["background"],
        },
    )
    if created:
        user.set_password(DEMO_PASSWORD)
        user.save()
    else:
        user.email = member["email"]
        user.role = role
        user.qualifications = member["qualifications"]
        user.background = member["background"]
        user.save()
    team_users[member["username"]] = user
    EngagementMembership.objects.get_or_create(engagement=engagement, user=user)
print(f"Assessment team: {len(TEAM)} members ({', '.join(u.get_full_name() for u in team_users.values())})")


# ------------------------------------------------------------------ status history

STATUS_HISTORY = [   ('IN_PROGRESS', 'Morgan Blake'),
    ('IN_REVIEW', 'Taylor Reed'),
    ('QA', 'Robin Chen'),
    ('APPROVED', 'Morgan Blake')]

# changed_at is auto_now_add, so a normal .create() always stamps "now" --
# .update() afterwards backdates it without re-triggering that.
EngagementStatusHistory.objects.filter(engagement=engagement).delete()
base_time = timezone.now()
_user_by_full_name = {u.get_full_name(): u for u in team_users.values()}
for status, changed_by_name in STATUS_HISTORY:
    changed_by = _user_by_full_name.get(changed_by_name)
    row = EngagementStatusHistory.objects.create(engagement=engagement, status=status, changed_by=changed_by)
    EngagementStatusHistory.objects.filter(pk=row.pk).update(changed_at=base_time)
print(f"Status history: {len(STATUS_HISTORY)} entries")


# ------------------------------------------------------------------ findings

FINDINGS = [   {   'display_id': '',
        'title': 'Cross Site Request Forgery on Password Reset Form',
        'severity': 'MEDIUM',
        'status': 'OPEN',
        'cvss_score': '5.1',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://docs.redscribe.app/api/v1/user/password/reset',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A06:2025 – Insecure Design']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the technical evaluation of {{ scope }}, '
                                                     'assessors identified a cross site request '
                                                     'forgery vulnerability within the user '
                                                     'password reset functionality. The web '
                                                     'application accepts state changing requests '
                                                     'to update account passwords without '
                                                     'validating an anti cross site request '
                                                     'forgery token or requiring reauthentication '
                                                     'using the current password."}]}, {"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "When '
                                                     'an authenticated user visits an attacker '
                                                     'controlled website while maintaining an '
                                                     'active session with {{ scope }}, the '
                                                     'malicious site can submit an automated '
                                                     'background request to the password reset '
                                                     'endpoint. Because the application relies '
                                                     'solely on ambient browser authentication '
                                                     'credentials such as session cookies, the '
                                                     'request executes within the context of the '
                                                     'victim account, allowing an attacker to '
                                                     'overwrite account passwords without the '
                                                     'target user knowledge or interaction beyond '
                                                     'visiting the malicious page."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "The '
                                                     'business impact is categorized as medium. '
                                                     'Successful exploitation allows an attacker '
                                                     'to compromise target user accounts, '
                                                     'resulting in unauthorized password '
                                                     'modification and subsequent account takeover '
                                                     'across operational roles such as Consultant '
                                                     'or Senior Consultant. However, exploitation '
                                                     'requires victim interaction, such as '
                                                     'convincing an authenticated user to visit a '
                                                     'malicious third party link while logged into '
                                                     'the application."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Verification was performed by '
                                            'crafting an external HTML document containing an '
                                            'automated form submission targeted at the password '
                                            'reset endpoint."}]}, {"type": "paragraph", "attrs": '
                                            '{"lead": false}, "content": [{"type": "text", "text": '
                                            '"Attacker controlled Proof-of-Concept(PoC) web '
                                            'page"}]}, {"type": "codeBlock", "attrs": {"language": '
                                            'null}, "content": [{"type": "text", "text": '
                                            '"<html>\\n  <body>\\n    <form id=\\"csrfForm\\" '
                                            'action=\\"https://docs.redscribe.app/api/v1/user/password/reset\\" '
                                            'method=\\"POST\\">\\n      <input type=\\"hidden\\" '
                                            'name=\\"new_password\\" '
                                            'value=\\"AttackerP@ssword123!\\" />\\n      <input '
                                            'type=\\"hidden\\" name=\\"confirm_password\\" '
                                            'value=\\"AttackerP@ssword123!\\" />\\n    '
                                            '</form>\\n    <script>\\n      '
                                            "document.getElementById('csrfForm').submit();\\n    "
                                            '</script>\\n  </body>\\n</html>"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "HTTP request transmitted '
                                            'by the web application"}]}, {"type": "codeBlock", '
                                            '"attrs": {"language": null}, "content": [{"type": '
                                            '"text", "text": "POST "}, {"type": "text", "marks": '
                                            '[{"type": "highlight"}], "text": '
                                            '"/api/v1/user/password/reset"}, {"type": "text", '
                                            '"text": " HTTP/1.1\\nHost: '
                                            'docs.redscribe.app\\nUser-Agent: Mozilla/5.0 (Windows '
                                            'NT 10.0; Win64; x64)\\nContent-Type: '
                                            'application/x-www-form-urlencoded\\nCookie: '
                                            'session_id=xyz123456789abc\\n\\nnew_password=AttackerP@ssword123!&confirm_password=AttackerP@ssword123!"}]}, '
                                            '{"type": "paragraph", "attrs": {"lead": false}, '
                                            '"content": [{"type": "text", "text": "HTTP '
                                            'response:"}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"marks": [{"type": "highlight"}], "text": "HTTP/1.1 '
                                            '200 OK"}, {"type": "text", "text": "\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"status\\": \\""}, '
                                            '{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "success"}, {"type": "text", "text": '
                                            '"\\",\\n  \\"message\\": \\""}, {"type": "text", '
                                            '"marks": [{"type": "highlight"}], "text": "Password '
                                            'successfully updated"}, {"type": "text", "text": '
                                            '"\\"\\n}"}]}, {"type": "paragraph", "attrs": {"lead": '
                                            'false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"text": "{{ client_name }} should implement unpredictable '
                                        'cryptographically secure anti cross site request forgery '
                                        'tokens for all state changing HTTP requests within the '
                                        'application. These tokens must be tied to the current '
                                        'user session, validated on the server side upon form '
                                        'submission, and rejected if absent or mismatched."}]}, '
                                        '{"type": "paragraph", "attrs": {"lead": false}, '
                                        '"content": [{"type": "text", "text": "Additionally, '
                                        'sensitive security operations such as password changes, '
                                        'email address updates, and authentication credential '
                                        'modifications should mandate reauthentication by '
                                        'requiring the user to supply their existing password '
                                        'prior to processing the request. Setting the SameSite '
                                        'cookie attribute to Lax or Strict across all session '
                                        'cookies provides an effective defense in depth '
                                        'mechanism."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following references provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "OWASP Cross Site '
                                      'Request Forgery Prevention Cheat Sheet"}]}]}]}, {"type": '
                                      '"paragraph", "attrs": {"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Broken Access Control Allowing Horizontal Privilege Escalation in Billing Portal',
        'severity': 'MEDIUM',
        'status': 'OPEN',
        'cvss_score': '5.3',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://redscribe.app/api/v1/billing/profiles?account_id={numerical_id}',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A01:2025 – Broken Access Control']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the assessment, a broken access control '
                                                     'vulnerability was identified within the '
                                                     'billing portal on "}, {"type": "text", '
                                                     '"marks": [{"type": "link", "attrs": {"href": '
                                                     '"http://redscribe.app", "target": "_blank", '
                                                     '"rel": "noopener noreferrer nofollow", '
                                                     '"class": null, "title": null}}], "text": '
                                                     '"redscribe.app"}, {"type": "text", "text": '
                                                     '". The application fails to properly '
                                                     'validate whether an authenticated user '
                                                     'possesses the authorization to access or '
                                                     'modify billing records associated with other '
                                                     'tenant accounts."}]}, {"type": "paragraph", '
                                                     '"attrs": {"lead": false}, "content": '
                                                     '[{"type": "text", "text": "By manipulating '
                                                     'the integer account identifier ("}, {"type": '
                                                     '"text", "marks": [{"type": "code"}], "text": '
                                                     '"account_id"}, {"type": "text", "text": ") '
                                                     'sent within the HTTP request parameters, an '
                                                     'authenticated attacker can view sensitive '
                                                     'billing information, subscription tiers, '
                                                     'payment histories, and partial credit card '
                                                     'details belonging to other registered users. '
                                                     'This defect represents a classic insecure '
                                                     'direct object reference condition leading to '
                                                     'horizontal privilege escalation across '
                                                     'tenant boundaries."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Exploitation of this issue allows an '
                                                     'authenticated attacker to systematically '
                                                     'iterate through valid account identifiers to '
                                                     'gain unauthorized access to sensitive '
                                                     'financial and personally identifiable '
                                                     'information across all users on the '
                                                     'platform. Beyond data confidentiality breach '
                                                     'risks, compromised account metadata can be '
                                                     'leveraged to craft highly targeted social '
                                                     'engineering campaigns against affected '
                                                     'organization administrators."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "The vulnerability was demonstrated '
                                            'by authenticating as a standard user ("}, {"type": '
                                            '"text", "marks": [{"type": "code"}], "text": '
                                            '"user_a"}, {"type": "text", "text": ") and attempting '
                                            'to access the billing profile endpoint using an '
                                            'identifier assigned to another user ("}, {"type": '
                                            '"text", "marks": [{"type": "code"}], "text": '
                                            '"user_b"}, {"type": "text", "text": ")."}]}, {"type": '
                                            '"bulletList", "content": [{"type": "listItem", '
                                            '"content": [{"type": "paragraph", "attrs": {"lead": '
                                            'false}, "content": [{"type": "text", "text": '
                                            '"Authenticated as "}, {"type": "text", "marks": '
                                            '[{"type": "code"}], "text": "user_a"}, {"type": '
                                            '"text", "text": " and intercepted the request to '
                                            'retrieve account billing details:"}]}]}]}, {"type": '
                                            '"codeBlock", "attrs": {"language": null}, "content": '
                                            '[{"type": "text", "text": "GET '
                                            '/api/v1/billing/profiles?account_id=1042 '
                                            'HTTP/1.1\\nHost: redscribe.app\\nAuthorization: '
                                            'Bearer <user_a_token>"}]}, {"type": "bulletList", '
                                            '"content": [{"type": "listItem", "content": [{"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "Modified the parameter '
                                            'value to target "}, {"type": "text", "marks": '
                                            '[{"type": "code"}], "text": "account_id=1041"}, '
                                            '{"type": "text", "text": " (belonging to "}, {"type": '
                                            '"text", "marks": [{"type": "code"}], "text": '
                                            '"user_b"}, {"type": "text", "text": "):"}]}]}]}, '
                                            '{"type": "codeBlock", "attrs": {"language": null}, '
                                            '"content": [{"type": "text", "text": "GET '
                                            '/api/v1/billing/profiles?account_id=1041 '
                                            'HTTP/1.1\\nHost: redscribe.app\\nAuthorization: '
                                            'Bearer <user_a_token>"}]}, {"type": "bulletList", '
                                            '"content": [{"type": "listItem", "content": [{"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "The server responded with '
                                            'a "}, {"type": "text", "marks": [{"type": "code"}], '
                                            '"text": "200 OK"}, {"type": "text", "text": " HTTP '
                                            'status code containing the full billing profile data '
                                            'for "}, {"type": "text", "marks": [{"type": "code"}], '
                                            '"text": "user_b"}, {"type": "text", "text": '
                                            '":"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"marks": [{"type": "highlight"}], "text": "HTTP/1.1 '
                                            '200 OK"}, {"type": "text", "text": "\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"account_id\\": '
                                            '1041,\\n  \\"organization_name\\": \\"Acme '
                                            'Corp\\",\\n  \\"billing_contact\\": '
                                            '\\"admin@acmecorp.example\\",\\n  '
                                            '\\"subscription_status\\": \\"Active\\",\\n  '
                                            '\\"payment_method\\": {\\n    \\"card_type\\": '
                                            '\\"Visa\\",\\n    \\"last_four\\": \\"4321\\",\\n    '
                                            '\\"expiry\\": \\"11/28\\"\\n  }\\n}"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Implement Server '
                                        'Side Access Control Checks:"}, {"type": "text", "text": " '
                                        'Ensure that every request involving object identifiers '
                                        'performs explicit authorization checks on the server side '
                                        'to verify that the requesting session identity owns or '
                                        'has explicit permission to access the requested '
                                        'resource."}]}, {"type": "paragraph", "attrs": {"lead": '
                                        'false}, "content": [{"type": "text", "marks": [{"type": '
                                        '"bold"}], "text": "Use Indirect or Non Sequential '
                                        'References:"}, {"type": "text", "text": " Replace '
                                        'predictable sequential identifiers ("}, {"type": "text", '
                                        '"marks": [{"type": "code"}], "text": "account_id=1041"}, '
                                        '{"type": "text", "text": ") with cryptographically secure '
                                        'random identifiers, such as version 4 Universally Unique '
                                        'Identifiers (UUIDs), to prevent enumeration attacks."}]}, '
                                        '{"type": "paragraph", "attrs": {"lead": false}, '
                                        '"content": [{"type": "text", "marks": [{"type": "bold"}], '
                                        '"text": "Centralize Authorization Rules:"}, {"type": '
                                        '"text", "text": " Enforce access control mechanisms '
                                        'within the data access layer or middleware rather than '
                                        'relying on decentralized parameter checks across '
                                        'individual API endpoints."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resource provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"http://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "Authorization '
                                      'Cheat Sheet | OWASP"}]}]}]}, {"type": "paragraph", "attrs": '
                                      '{"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Insecure Direct Object Reference Leading to PII Disclosure',
        'severity': 'HIGH',
        'status': 'OPEN',
        'cvss_score': '7.1',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://docs.redscribe.app/api/v2/users/{user.id}/export',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A01:2025 – Broken Access Control']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the security assessment, an insecure direct '
                                                     'object reference vulnerability was '
                                                     'identified within the documentation portal '
                                                     'on "}, {"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "docs.redscribe.app"}, '
                                                     '{"type": "text", "text": ". The application '
                                                     'exposes REST API endpoints for user '
                                                     'documentation preferences and exported '
                                                     'account data that rely on predictable object '
                                                     'identifiers without performing adequate '
                                                     'authorization validation."}]}, {"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "An '
                                                     'authenticated attacker can manipulate user '
                                                     'record parameters (such as "}, {"type": '
                                                     '"text", "marks": [{"type": "code"}], "text": '
                                                     '"user_id"}, {"type": "text", "text": " or '
                                                     '"}, {"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "profile_id"}, {"type": '
                                                     '"text", "text": ") sent in API requests to '
                                                     'retrieve sensitive personally identifiable '
                                                     'information belonging to other platform '
                                                     'users. The server processes these requests '
                                                     'based solely on the validity of the session '
                                                     'token rather than verifying that the '
                                                     'requesting user owns the requested '
                                                     'resource."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Exploitation of this vulnerability allows '
                                                     'an authenticated attacker to systematically '
                                                     'iterate through numerical or predictable '
                                                     'user identifiers to harvest customer data. '
                                                     'Exfiltrated records include full names, '
                                                     'email addresses, phone numbers, '
                                                     'organizational roles, and internal account '
                                                     'preferences."}]}, {"type": "paragraph", '
                                                     '"attrs": {"lead": false}, "content": '
                                                     '[{"type": "text", "text": "Mass disclosure '
                                                     'of personally identifiable information '
                                                     'introduces severe regulatory compliance '
                                                     'risks under the Australian Privacy Act and '
                                                     'Privacy Amendment (Notifiable Data Breaches) '
                                                     'scheme, alongside exposing affected '
                                                     'individuals to targeted phishing and '
                                                     'identity theft risks."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "The vulnerability was verified by '
                                            'capturing an API request intended to retrieve '
                                            'personal profile exports on "}, {"type": "text", '
                                            '"marks": [{"type": "code"}], "text": '
                                            '"docs.redscribe.app"}, {"type": "text", "text": '
                                            '"."}]}, {"type": "paragraph", "attrs": {"lead": '
                                            'false}, "content": [{"type": "text", "text": '
                                            '"Authenticated as a standard user ("}, {"type": '
                                            '"text", "marks": [{"type": "code"}], "text": '
                                            '"user_108"}, {"type": "text", "text": ") and '
                                            'initiated a request to retrieve personal account '
                                            'settings and export records:"}]}, {"type": '
                                            '"codeBlock", "attrs": {"language": null}, "content": '
                                            '[{"type": "text", "text": "GET '
                                            '/api/v2/users/108/export HTTP/1.1\\nHost: '
                                            'docs.redscribe.app\\nAuthorization: Bearer '
                                            '<authenticated_user_token>\\nAccept: '
                                            'application/json"}]}, {"type": "paragraph", "attrs": '
                                            '{"lead": false}, "content": [{"type": "text", "text": '
                                            '"Intercepted the traffic and modified the endpoint '
                                            'identifier to target "}, {"type": "text", "marks": '
                                            '[{"type": "code"}], "text": "user_109"}, {"type": '
                                            '"text", "text": ":"}]}, {"type": "codeBlock", '
                                            '"attrs": {"language": null}, "content": [{"type": '
                                            '"text", "text": "GET /api/v2/users/"}, {"type": '
                                            '"text", "marks": [{"type": "highlight"}], "text": '
                                            '"109"}, {"type": "text", "text": "/export '
                                            'HTTP/1.1\\nHost: docs.redscribe.app\\nAuthorization: '
                                            'Bearer <authenticated_user_token>\\nAccept: '
                                            'application/json"}]}, {"type": "paragraph", "attrs": '
                                            '{"lead": false}, "content": [{"type": "text", "text": '
                                            '"The server processed the request without validating '
                                            'object ownership, returning a "}, {"type": "text", '
                                            '"marks": [{"type": "code"}], "text": "200 OK"}, '
                                            '{"type": "text", "text": " HTTP response containing '
                                            'the personally identifiable information of "}, '
                                            '{"type": "text", "marks": [{"type": "code"}], "text": '
                                            '"user_109"}, {"type": "text", "text": ":"}]}, '
                                            '{"type": "codeBlock", "attrs": {"language": null}, '
                                            '"content": [{"type": "text", "marks": [{"type": '
                                            '"highlight"}], "text": "HTTP/1.1 200 OK"}, {"type": '
                                            '"text", "text": "\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"user_id\\": 109,\\n  '
                                            '\\"full_name\\": \\"Jane Doe\\",\\n  \\"email\\": '
                                            '\\"j.doe@example.com.au\\",\\n  \\"phone\\": \\"+61 '
                                            '412 345 678\\",\\n  \\"organization\\": \\"Partner '
                                            'Enterprise AU\\",\\n  \\"role\\": \\"Documentation '
                                            'Manager\\",\\n  \\"created_at\\": \\"2026 01 '
                                            '15T08:30:00Z\\"\\n}"}]}, {"type": "paragraph", '
                                            '"attrs": {"lead": false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Enforce Context '
                                        'Aware Authorization:"}, {"type": "text", "text": " '
                                        'Implement contextual server side authorization checks to '
                                        'verify that the authenticated identity bound to the '
                                        'session token possesses explicit permission to access the '
                                        'requested resource identifier."}]}, {"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Utilize '
                                        'Cryptographically Secure Identifiers:"}, {"type": "text", '
                                        '"text": " Replace sequential integer keys ("}, {"type": '
                                        '"text", "marks": [{"type": "code"}], "text": '
                                        '"/users/109/"}, {"type": "text", "text": ") with '
                                        'cryptographically random version 4 Universally Unique '
                                        'Identifiers (UUIDs) across all public facing API routes '
                                        'to impede automated resource enumeration."}]}, {"type": '
                                        '"paragraph", "attrs": {"lead": false}, "content": '
                                        '[{"type": "text", "marks": [{"type": "bold"}], "text": '
                                        '"Adopt Indirect Data Mapping:"}, {"type": "text", "text": '
                                        '" Map session identifiers directly to user data on the '
                                        'server side where applicable, removing the requirement to '
                                        'accept user supplied object keys in API endpoints (e.g. '
                                        'replacing "}, {"type": "text", "marks": [{"type": '
                                        '"code"}], "text": "/users/109/export"}, {"type": "text", '
                                        '"text": " with "}, {"type": "text", "marks": [{"type": '
                                        '"code"}], "text": "/users/me/export"}, {"type": "text", '
                                        '"text": ")."}]}, {"type": "paragraph", "attrs": {"lead": '
                                        'false}}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resource provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": '
                                      '"OWASP Top 10: A01:2025 Broken Access Control"}]}]}, '
                                      '{"type": "listItem", "content": [{"type": "paragraph", '
                                      '"attrs": {"lead": false}, "content": [{"type": "text", '
                                      '"marks": [{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "Authorization '
                                      'Cheat Sheet | OWASP"}]}]}]}, {"type": "paragraph", "attrs": '
                                      '{"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'SQL Injection',
        'severity': 'HIGH',
        'status': 'OPEN',
        'cvss_score': '8.6',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://redscribe.app/api/v1/docs/search?query=billing&category=',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A05:2025 – Injection']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the assessment, an inline SQL injection '
                                                     'vulnerability was identified within the '
                                                     'documentation search filter functionality on '
                                                     '"}, {"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "redscribe.app"}, {"type": '
                                                     '"text", "text": ". The application appends '
                                                     'user supplied input from the query parameter '
                                                     'directly into a dynamic SQL query string '
                                                     'without performing parameterisation or input '
                                                     'sanitisation."}]}, {"type": "paragraph", '
                                                     '"attrs": {"lead": false}, "content": '
                                                     '[{"type": "text", "text": "An authenticated '
                                                     'attacker can manipulate the "}, {"type": '
                                                     '"text", "marks": [{"type": "code"}], "text": '
                                                     '"category"}, {"type": "text", "text": " '
                                                     'filter parameter in requests sent to the '
                                                     'search API to inject arbitrary SQL '
                                                     'statements. The backend database server '
                                                     'executes these modified queries under the '
                                                     'context of the application database user '
                                                     'account."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Exploitation of this vulnerability allows '
                                                     'an attacker to bypass application access '
                                                     'controls and extract the entire content of '
                                                     'the underlying relational database, '
                                                     'including hashed user credentials, session '
                                                     'tokens, and sensitive tenant configuration '
                                                     'records."}]}, {"type": "paragraph", "attrs": '
                                                     '{"lead": false}, "content": [{"type": '
                                                     '"text", "text": "Depending on database '
                                                     'engine permissions, an attacker may also '
                                                     'modify, insert, or delete database records, '
                                                     'potentially causing widespread data '
                                                     'corruption or completely compromising '
                                                     'application integrity across the entire '
                                                     'platform."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "The vulnerability was demonstrated '
                                            'by injecting time based and boolean SQL payloads into '
                                            'the "}, {"type": "text", "marks": [{"type": "code"}], '
                                            '"text": "category"}, {"type": "text", "text": " '
                                            'parameter of the documentation search API '
                                            'endpoint."}]}, {"type": "bulletList", "content": '
                                            '[{"type": "listItem", "content": [{"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "Issued a baseline request '
                                            'to the search endpoint using a legitimate category '
                                            'parameter value:"}]}]}]}, {"type": "codeBlock", '
                                            '"attrs": {"language": null}, "content": [{"type": '
                                            '"text", "text": "GET '
                                            '/api/v1/docs/search?query=billing&category=user_guides '
                                            'HTTP/1.1\\nHost: redscribe.app\\nAuthorization: '
                                            'Bearer <authenticated_user_token>"}]}, {"type": '
                                            '"bulletList", "content": [{"type": "listItem", '
                                            '"content": [{"type": "paragraph", "attrs": {"lead": '
                                            'false}, "content": [{"type": "text", "text": '
                                            '"Injected a SQL payload designed to force a '
                                            'conditional time delay ("}, {"type": "text", "marks": '
                                            '[{"type": "code"}], "text": "OR SLEEP(5)--"}, '
                                            '{"type": "text", "text": ") into the '
                                            'parameter:"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "GET '
                                            '/api/v1/docs/search?query=billing&category=user_guides"}, '
                                            '{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "\'+OR+SLEEP(5)--"}, {"type": "text", "text": '
                                            '" HTTP/1.1\\nHost: redscribe.app\\nAuthorization: '
                                            'Bearer <authenticated_user_token>"}]}, {"type": '
                                            '"bulletList", "content": [{"type": "listItem", '
                                            '"content": [{"type": "paragraph", "attrs": {"lead": '
                                            'false}, "content": [{"type": "text", "text": "The '
                                            'backend server executed the injected database '
                                            'command, causing the HTTP response time to '
                                            'intentionally delay by 5.08 seconds before returning '
                                            'a "}, {"type": "text", "marks": [{"type": "code"}], '
                                            '"text": "200 OK"}, {"type": "text", "text": " status '
                                            'code."}]}]}, {"type": "listItem", "content": '
                                            '[{"type": "paragraph", "attrs": {"lead": false}, '
                                            '"content": [{"type": "text", "text": "Further testing '
                                            'confirmed data extraction capabilities by appending a '
                                            '"}, {"type": "text", "marks": [{"type": "code"}], '
                                            '"text": "UNION SELECT"}, {"type": "text", "text": " '
                                            'query payload to dump database schema '
                                            'details:"}]}]}]}, {"type": "paragraph", "attrs": '
                                            '{"lead": false}, "content": [{"type": "text", "text": '
                                            '"HTTP request:"}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "GET '
                                            '/api/v1/docs/search?query=billing&category=user_guides"}, '
                                            '{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "\'+UNION+SELECT+1,version(),user(),4--"}, '
                                            '{"type": "text", "text": " HTTP/1.1\\nHost: '
                                            'redscribe.app\\nAuthorization: Bearer '
                                            '<authenticated_user_token>"}]}, {"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "HTTP response:"}]}, {"type": '
                                            '"codeBlock", "attrs": {"language": null}, "content": '
                                            '[{"type": "text", "text": "HTTP/1.1 200 '
                                            'OK\\nContent-Type: application/json\\n\\n{\\n  '
                                            '\\"results\\": [\\n    {\\n      \\"id\\": 1,\\n      '
                                            '\\"title\\": \\""}, {"type": "text", "marks": '
                                            '[{"type": "highlight"}], "text": "PostgreSQL 15.3 on '
                                            'x86_64-pc-linux-gnu"}, {"type": "text", "text": '
                                            '"\\",\\n      \\"author\\": \\""}, {"type": "text", '
                                            '"marks": [{"type": "highlight"}], "text": '
                                            '"app_rw_user@10.0.4.12"}, {"type": "text", "text": '
                                            '"\\",\\n      \\"category\\": \\"4\\"\\n    }\\n  '
                                            ']\\n}"}]}, {"type": "paragraph", "attrs": {"lead": '
                                            'false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Use Parameterised '
                                        'Database Queries:"}, {"type": "text", "text": " Replace '
                                        'all dynamically constructed string queries with '
                                        'parameterised queries or prepared statements across the '
                                        'data access layer."}]}, {"type": "paragraph", "attrs": '
                                        '{"lead": false}, "content": [{"type": "text", "marks": '
                                        '[{"type": "bold"}], "text": "Utilize Object Relational '
                                        'Mapping (ORM) Framework Safety:"}, {"type": "text", '
                                        '"text": " Ensure ORM queries strictly use parameter '
                                        'binding mechanisms and avoid passing raw user input into '
                                        'native query escape functions."}]}, {"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Apply the Principle '
                                        'of Least Privilege:"}, {"type": "text", "text": " '
                                        'Restrict the backend database service user account '
                                        'permissions so that it can only access required tables '
                                        'and functions, prohibiting administrative commands or '
                                        'system file operations."}]}, {"type": "paragraph", '
                                        '"attrs": {"lead": false}}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resources provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "Injection '
                                      'Prevention Cheat Sheet | OWASP"}]}]}]}, {"type": '
                                      '"paragraph", "attrs": {"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Authentication Bypass via Missing JWT Signature Validation',
        'severity': 'CRITICAL',
        'status': 'OPEN',
        'cvss_score': '9.3',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://redscribe.app/api/v1/*',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A07:2025 – Authentication Failures']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the security assessment, a critical '
                                                     'authentication bypass vulnerability was '
                                                     'identified across API endpoints on "}, '
                                                     '{"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "redscribe.app"}, {"type": '
                                                     '"text", "text": ". The backend application '
                                                     'processes JSON Web Tokens (JWT) supplied '
                                                     'within the HTTP "}, {"type": "text", '
                                                     '"marks": [{"type": "code"}], "text": '
                                                     '"Authorization"}, {"type": "text", "text": " '
                                                     'bearer header to authenticate users, but it '
                                                     'fails to perform cryptographic signature '
                                                     'validation before accepting claims."}]}, '
                                                     '{"type": "paragraph", "attrs": {"lead": '
                                                     'false}, "content": [{"type": "text", "text": '
                                                     '"An unauthenticated attacker can forge '
                                                     'arbitrary JWTs by altering payload claims '
                                                     '(such as "}, {"type": "text", "marks": '
                                                     '[{"type": "code"}], "text": "sub"}, {"type": '
                                                     '"text", "text": ", "}, {"type": "text", '
                                                     '"marks": [{"type": "code"}], "text": '
                                                     '"role"}, {"type": "text", "text": ", or "}, '
                                                     '{"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "email"}, {"type": "text", '
                                                     '"text": ") and appending an invalid '
                                                     'signature, setting the signature algorithm '
                                                     'to "}, {"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "none"}, {"type": "text", '
                                                     '"text": ", or completely stripping the '
                                                     'signature block. Because the server trusts '
                                                     'the token payload contents without verifying '
                                                     'cryptographic authenticity, arbitrary user '
                                                     'identity spoofing and administrative access '
                                                     'can be achieved."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Exploitation of this flaw completely '
                                                     'compromises the application security '
                                                     'perimeter. An unauthenticated remote '
                                                     'attacker can forge valid tokens for any '
                                                     'registered platform user, including site '
                                                     'administrators or system operators."}]}, '
                                                     '{"type": "paragraph", "attrs": {"lead": '
                                                     'false}, "content": [{"type": "text", "text": '
                                                     '"Successful exploitation grants full '
                                                     'administrative control over application '
                                                     'functionalities, permitting unrestricted '
                                                     'access to sensitive tenant data, '
                                                     'administrative configuration panels, and '
                                                     'database modification endpoints across all '
                                                     'hosted organizations."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "The vulnerability was verified by '
                                            'crafting a forged JSON Web Token containing '
                                            'administrator claims without providing a valid '
                                            'cryptographic signature."}]}, {"type": "bulletList", '
                                            '"content": [{"type": "listItem", "content": [{"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "Decoded a standard low '
                                            'privilege user token to examine the claim '
                                            'structure:"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "Header:\\n{\\n  \\"alg\\": \\"HS256\\",\\n  '
                                            '\\"typ\\": \\"JWT\\"\\n}\\n\\nPayload:\\n{\\n  '
                                            '\\"sub\\": \\"user_1042\\",\\n  \\"email\\": '
                                            '\\"standard_user@redscribe.app\\",\\n  \\"role\\": '
                                            '\\"User\\",\\n  \\"iat\\": 1773968685\\n}"}]}, '
                                            '{"type": "bulletList", "content": [{"type": '
                                            '"listItem", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Modified the payload claims to '
                                            'elevate privileges to an administrative user ("}, '
                                            '{"type": "text", "marks": [{"type": "code"}], "text": '
                                            '"role: Admin"}, {"type": "text", "text": "), updated '
                                            'the algorithm header field to "}, {"type": "text", '
                                            '"marks": [{"type": "code"}], "text": "none"}, '
                                            '{"type": "text", "text": ", and omitted the signature '
                                            'segment:"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "Header '
                                            '(Base64URL):\\neyJhbGciOiJub25lIiwidHlwIjoiSldUIn0\\n\\nPayload '
                                            '(Base64URL):\\neyJzdWIiOiJ1c2VyXzAwMSIsImVtYWlsIjoiYWRtaW5AcmVkc2NyaWJlLmFwcCIsInJvbGUiOiJBZG1pbiIsImlhdCI6MTc3Mzk2ODY4NX0\\n\\nForged '
                                            'Token:\\neyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyXzAwMSIsImVtYWlsIjoiYWRtaW5AcmVkc2NyaWJlLmFwcCIsInJvbGUiOiJBZG1pbiIsImlhdCI6MTc3Mzk2ODY4NX0."}]}, '
                                            '{"type": "bulletList", "content": [{"type": '
                                            '"listItem", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Issued a request to an '
                                            'administrative API endpoint using the forged '
                                            'token:"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "GET /api/v1/admin/users HTTP/1.1\\nHost: '
                                            'redscribe.app\\nAuthorization: Bearer '
                                            'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyXzAwMSIsImVtYWlsIjoiYWRtaW5AcmVkc2NyaWJlLmFwcCIsInJvbGUiOiJBZG1pbiIsImlhdCI6MTc3Mzk2ODY4NX0.\\nAccept: '
                                            'application/json"}]}, {"type": "bulletList", '
                                            '"content": [{"type": "listItem", "content": [{"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "The server accepted the '
                                            'unverified token without error, returning a "}, '
                                            '{"type": "text", "marks": [{"type": "code"}], "text": '
                                            '"200 OK"}, {"type": "text", "text": " status code '
                                            'alongside administrative data:"}]}]}]}, {"type": '
                                            '"codeBlock", "attrs": {"language": null}, "content": '
                                            '[{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "HTTP/1.1 200 OK"}, {"type": "text", "text": '
                                            '"\\nContent-Type: application/json\\n\\n{\\n  '
                                            '\\"status\\": \\""}, {"type": "text", "marks": '
                                            '[{"type": "highlight"}], "text": "success"}, {"type": '
                                            '"text", "text": "\\",\\n  \\"authenticated_as\\": "}, '
                                            '{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "\\"admin@redscribe.app\\""}, {"type": '
                                            '"text", "text": ",\\n  \\"role\\": \\""}, {"type": '
                                            '"text", "marks": [{"type": "highlight"}], "text": '
                                            '"Admin"}, {"type": "text", "text": "\\",\\n  '
                                            '\\"users_count\\": 1420\\n}"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Enforce Mandatory '
                                        'JWT Signature Validation:"}, {"type": "text", "text": " '
                                        'Configure server side JWT libraries to strictly verify '
                                        'token signatures using strong secret keys or public key '
                                        'infrastructure before processing token claims."}]}, '
                                        '{"type": "paragraph", "attrs": {"lead": false}, '
                                        '"content": [{"type": "text", "marks": [{"type": "bold"}], '
                                        '"text": "Explicitly Restrict Signing Algorithms:"}, '
                                        '{"type": "text", "text": " Reject tokens that specify '
                                        'unsafe signing algorithms such as "}, {"type": "text", '
                                        '"marks": [{"type": "code"}], "text": "none"}, {"type": '
                                        '"text", "text": ", or algorithms that mismatch expected '
                                        'secret key types (e.g. enforcing HMAC or RSA validation '
                                        'explicitly)."}]}, {"type": "paragraph", "attrs": {"lead": '
                                        'false}, "content": [{"type": "text", "marks": [{"type": '
                                        '"bold"}], "text": "Use Established Security '
                                        'Frameworks:"}, {"type": "text", "text": " Avoid custom '
                                        'JWT verification logic and rely on well audited, up to '
                                        'date authentication libraries configured to enforce '
                                        'strict token validation policies."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resources provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "JSON Web Token '
                                      'Cheat Sheet | OWASP"}]}]}]}, {"type": "paragraph", "attrs": '
                                      '{"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Reflected Cross Site Scripting in Search Query Parameter',
        'severity': 'MEDIUM',
        'status': 'OPEN',
        'cvss_score': '5.1',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://docs.redscribe.app/search?q=',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A05:2025 – Injection']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the technical evaluation of {{ scope }}, '
                                                     'assessors identified a reflected cross site '
                                                     'scripting vulnerability within the primary '
                                                     'application search module. User input '
                                                     'supplied to the search query parameter is '
                                                     'reflected directly into the application '
                                                     'Document Object Model response without '
                                                     'adequate context aware output encoding or '
                                                     'input sanitization."}]}, {"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "When a '
                                                     'user submits a specially crafted input '
                                                     'string containing client side script '
                                                     'payloads, the backend web server '
                                                     'incorporates the payload directly into the '
                                                     'rendered HTML body. Because the browser '
                                                     'interprets the returned markup as trusted '
                                                     'application executable code, arbitrary '
                                                     'JavaScript executes within the security '
                                                     'context of the victim browser session."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "The '
                                                     'business impact is evaluated as medium. '
                                                     'Successful exploitation allows an attacker '
                                                     'to execute arbitrary client side script code '
                                                     'in the context of the victim session. An '
                                                     'attacker who convinces an authenticated user '
                                                     'to follow a crafted link can hijack active '
                                                     'session identifiers, manipulate page content '
                                                     'displayed to the user, perform unauthorized '
                                                     'client side actions, or redirect users to '
                                                     'malicious external domains."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Verification was conducted by '
                                            'submitting HTML and JavaScript test payloads to the '
                                            'search query input parameter and observing reflected '
                                            'payload execution in the client browser."}]}, '
                                            '{"type": "paragraph", "attrs": {"lead": false}, '
                                            '"content": [{"type": "text", "text": "HTTP '
                                            'request:"}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "GET /search?q="}, {"type": "text", "marks": '
                                            '[{"type": "highlight"}], "text": '
                                            '"%3Cscript%3Ealert%28document.cookie%29%3C%2Fscript%3E"}, '
                                            '{"type": "text", "text": " HTTP/1.1\\nHost: '
                                            'docs.redscribe.app\\nUser-Agent: Mozilla/5.0 (Windows '
                                            'NT 10.0; Win64; x64)\\nAccept: '
                                            'text/html,application/xhtml+xml"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "HTTP response:"}]}, '
                                            '{"type": "codeBlock", "attrs": {"language": null}, '
                                            '"content": [{"type": "text", "text": "HTTP/1.1 200 '
                                            'OK\\nContent-Type: text/html; '
                                            'charset=utf-8\\n\\n<html>\\n  <body>\\n    <h2>Search '
                                            'Results for: "}, {"type": "text", "marks": [{"type": '
                                            '"highlight"}], "text": '
                                            '"<script>alert(document.cookie)</script>"}, {"type": '
                                            '"text", "text": "</h2>\\n    <p>No results found '
                                            'matching your criteria.</p>\\n  '
                                            '</body>\\n</html>"}]}, {"type": "paragraph", "attrs": '
                                            '{"lead": false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"text": "{{ client_name }} should implement strict, '
                                        'context aware output encoding across all application '
                                        'endpoints that reflect user controllable input back into '
                                        'response pages. Input rendered within HTML body elements '
                                        'must pass through HTML entity encoding functions prior to '
                                        'display."}]}, {"type": "paragraph", "attrs": {"lead": '
                                        'false}, "content": [{"type": "text", "text": "Where '
                                        'dynamic content requires insertion into script blocks or '
                                        'HTML attributes, context specific encoding functions such '
                                        'as JavaScript escaping or attribute encoding must be '
                                        'enforced. Furthermore, {{ client_name }} should deploy a '
                                        'strong Content Security Policy header restricting inline '
                                        'script execution and mandating secure script origins to '
                                        'provide robust defense in depth."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resources provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Preventive_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "OWASP Cross Site '
                                      'Scripting Prevention Cheat Sheet"}]}]}]}, {"type": '
                                      '"paragraph", "attrs": {"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Verbose Error Messages',
        'severity': 'INFORMATIONAL',
        'status': 'OPEN',
        'cvss_score': '0.0',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://docs.redscribe.app/',
        'workflow_status': 'QA_APPROVED',
        'classifications': [   [   'OWASP Top 10 2025',
                                   'A10:2025 – Mishandling of Exceptional Conditions']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the technical assessment of {{ scope }}, '
                                                     'assessors identified that the application '
                                                     'fails to handle operational exceptions '
                                                     'gracefully when receiving malformed requests '
                                                     'or invalid parameters. Instead of returning '
                                                     'generic user friendly error messages, the '
                                                     'backend application returns detailed stack '
                                                     'traces, internal code line numbers, database '
                                                     'query snippets, and underlying framework '
                                                     'version information directly to the '
                                                     'client."}]}, {"type": "paragraph", "attrs": '
                                                     '{"lead": false}, "content": [{"type": '
                                                     '"text", "text": "Uncaught exceptions and '
                                                     'verbose stack traces leak internal '
                                                     'operational context to potential attackers. '
                                                     'While the exposure of error details does not '
                                                     'directly permit data modification or '
                                                     'unauthorized access, it drastically reduces '
                                                     'the reconnaissance effort required for an '
                                                     'adversary to map application internals and '
                                                     'identify targeted exploitation '
                                                     'vectors."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "The '
                                                     'business impact associated with verbose '
                                                     'error messages is classified as '
                                                     'informational. The primary risk lies in '
                                                     'disclosing technical context, such as '
                                                     'database schemas, underlying framework '
                                                     'versions, and internal file paths. This '
                                                     'metadata provides potential attackers with '
                                                     'actionable insight into the software stack, '
                                                     'simplifying the development of tailored '
                                                     'attacks against specific component '
                                                     'vulnerabilities."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "During manual parameter tampering '
                                            'across API request structures, submitting invalid '
                                            'data types to database backed endpoints triggered '
                                            'verbose system exceptions."}]}, {"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "marks": [{"type": "bold"}], "text": "HTTP '
                                            'request:"}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "POST /api/v1/user/profile/lookup '
                                            'HTTP/1.1\\nHost: {{ scope }}\\nAuthorization: Bearer '
                                            '<valid_token>\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"user_id\\": \\"9999\' '
                                            'OR \'1\'=\'1\\"\\n}"}]}, {"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "marks": [{"type": "bold"}], "text": "HTTP '
                                            'response:"}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "HTTP/1.1 500 Internal Server '
                                            'Error\\nContent-Type: application/json\\n\\n{\\n  '
                                            '\\"status\\": \\"error\\",\\n  \\"message\\": '
                                            '\\"Unhandled Exception: "}, {"type": "text", "marks": '
                                            '[{"type": "highlight"}], "text": '
                                            '"System.Data.SqlClient.SqlException"}, {"type": '
                                            '"text", "text": "\\",\\n  \\"detail\\": \\"Unclosed '
                                            'quotation mark after the character string at query '
                                            'line 42 in /app/services/user_service.py\\",\\n  '
                                            '\\"stack_trace\\": [\\n    \\"File \'"}, {"type": '
                                            '"text", "marks": [{"type": "highlight"}], "text": '
                                            '"/app/services/user_service.py"}, {"type": "text", '
                                            '"text": "\', line 42, in get_user_by_id\\",\\n    '
                                            '\\"File \'"}, {"type": "text", "marks": [{"type": '
                                            '"highlight"}], "text": '
                                            '"/app/controllers/profile_controller.py"}, {"type": '
                                            '"text", "text": "\', line 18, in lookup\\"\\n  '
                                            ']\\n}"}]}, {"type": "paragraph", "attrs": {"lead": '
                                            'false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"text": "{{ client_name }} should implement global '
                                        'exception handling logic across the web application '
                                        'framework to intercept all runtime errors before they are '
                                        'rendered to the client. Detailed debugging logs and stack '
                                        'traces must be captured strictly in secure server side '
                                        'logs accessible only to system administrators."}]}, '
                                        '{"type": "paragraph", "attrs": {"lead": false}, '
                                        '"content": [{"type": "text", "text": "Client facing '
                                        'responses should return sanitized, generic error messages '
                                        'accompanied by a unique tracking reference code. This '
                                        'practice allows end users to report issues to technical '
                                        'support without exposing application infrastructure '
                                        'details. Furthermore, debug parameters and development '
                                        'modes must be explicitly disabled in all staging and '
                                        'production environments."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resources provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://owasp.org/www-project-top-ten/", "target": '
                                      '"_blank", "rel": "noopener noreferrer nofollow", "class": '
                                      'null, "title": null}}], "text": "OWASP Top 10 Information '
                                      'Disclosure"}]}]}, {"type": "listItem", "content": [{"type": '
                                      '"paragraph", "attrs": {"lead": false}, "content": [{"type": '
                                      '"text", "marks": [{"type": "link", "attrs": {"href": '
                                      '"https://cwe.mitre.org/data/definitions/209.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "CWE-209 '
                                      'Information Exposure Through an Error Message"}]}]}, '
                                      '{"type": "listItem", "content": [{"type": "paragraph", '
                                      '"attrs": {"lead": false}, "content": [{"type": "text", '
                                      '"marks": [{"type": "link", "attrs": {"href": '
                                      '"https://csrc.nist.gov/", "target": "_blank", "rel": '
                                      '"noopener noreferrer nofollow", "class": null, "title": '
                                      'null}}], "text": "NIST SP 800-53 Rev. 5 SI-11 Information '
                                      'Output Filtering"}]}]}]}, {"type": "paragraph", "attrs": '
                                      '{"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Missing Cookie Flags',
        'severity': 'LOW',
        'status': 'OPEN',
        'cvss_score': '2.3',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:H/AT:P/PR:N/UI:P/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://docs.redscribe.app/api/v1/login',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A02:2025 – Security Misconfiguration']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the technical evaluation of {{ scope }}, '
                                                     'assessors observed that session identifiers '
                                                     'and sensitive tracking cookies are issued '
                                                     'without vital security attributes, '
                                                     'specifically the "}, {"type": "text", '
                                                     '"marks": [{"type": "code"}], "text": '
                                                     '"Secure"}, {"type": "text", "text": ", "}, '
                                                     '{"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "HttpOnly"}, {"type": '
                                                     '"text", "text": ", and "}, {"type": "text", '
                                                     '"marks": [{"type": "code"}], "text": '
                                                     '"SameSite"}, {"type": "text", "text": " '
                                                     'flags. When the "}, {"type": "text", '
                                                     '"marks": [{"type": "code"}], "text": '
                                                     '"Secure"}, {"type": "text", "text": " '
                                                     'attribute is omitted, compliant web browsers '
                                                     'will transmit session cookies over '
                                                     'unencrypted HTTP connections if a user '
                                                     'accesses non HTTPS endpoints. Omitting the '
                                                     '"}, {"type": "text", "marks": [{"type": '
                                                     '"code"}], "text": "HttpOnly"}, {"type": '
                                                     '"text", "text": " flag allows client side '
                                                     'scripts to access session cookie values, '
                                                     'exposing tokens to extraction if cross site '
                                                     'scripting vulnerabilities exist within the '
                                                     'application domain."}]}, {"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Furthermore, omitting the "}, {"type": '
                                                     '"text", "marks": [{"type": "code"}], "text": '
                                                     '"SameSite"}, {"type": "text", "text": " '
                                                     'attribute or setting it to None without '
                                                     'appropriate restrictions allows browsers to '
                                                     'attach session cookies to cross origin '
                                                     'requests automatically. The absence of these '
                                                     'defensive cookie attributes undermines '
                                                     'defense in depth mechanisms and exposes user '
                                                     'session management to client side hijacking '
                                                     'and unauthorized request forgery."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "The '
                                                     'business impact is evaluated as low because '
                                                     'exploitation generally requires concurrent '
                                                     'client side attacks, such as cross site '
                                                     'scripting or network eavesdropping on '
                                                     'unencrypted channels. However, the absence '
                                                     'of these security flags increases the '
                                                     'overall attack surface by allowing '
                                                     'unauthorized client side access to sensitive '
                                                     'session tokens and facilitating session '
                                                     'hijacking if transport security is '
                                                     'compromised."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Inspection of HTTP response headers '
                                            'during authentication and session creation confirmed '
                                            'that sensitive session cookies were issued without '
                                            'the recommended security attributes."}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "HTTP request:"}]}, '
                                            '{"type": "codeBlock", "attrs": {"language": null}, '
                                            '"content": [{"type": "text", "text": "POST "}, '
                                            '{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "/api/v1/auth/login "}, {"type": "text", '
                                            '"text": "HTTP/1.1\\nHost: '
                                            'docs.redscribe.app\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"username\\": '
                                            '\\"consultant_user\\",\\n  \\"password\\": '
                                            '\\"ValidPassword123!\\"\\n}"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "HTTP response:"}]}, '
                                            '{"type": "codeBlock", "attrs": {"language": null}, '
                                            '"content": [{"type": "text", "text": "HTTP/1.1 200 '
                                            'OK\\nDate: Sun, 20 Sep 2026 00:00:00 GMT\\n"}, '
                                            '{"type": "text", "marks": [{"type": "highlight"}], '
                                            '"text": "Set-Cookie: session_id=xyz123456789abc; '
                                            'Path=/; Domain=docs.redscribe.app"}, {"type": "text", '
                                            '"text": "\\nContent-Type: application/json\\n\\n{\\n  '
                                            '"}, {"type": "text", "marks": [{"type": '
                                            '"highlight"}], "text": "\\"status\\": '
                                            '\\"success\\",\\n  \\"message\\": \\"Authentication '
                                            'successful\\""}, {"type": "text", "text": "\\n}"}]}, '
                                            '{"type": "paragraph", "attrs": {"lead": false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"text": "{{ client_name }} should update the web '
                                        'application configuration to ensure all sensitive session '
                                        'and state tracking cookies are issued with the "}, '
                                        '{"type": "text", "marks": [{"type": "code"}], "text": '
                                        '"Secure"}, {"type": "text", "text": ", "}, {"type": '
                                        '"text", "marks": [{"type": "code"}], "text": "HttpOnly"}, '
                                        '{"type": "text", "text": ", and "}, {"type": "text", '
                                        '"marks": [{"type": "code"}], "text": "SameSite"}, '
                                        '{"type": "text", "text": " attributes enabled."}]}, '
                                        '{"type": "paragraph", "attrs": {"lead": false}, '
                                        '"content": [{"type": "text", "text": "The "}, {"type": '
                                        '"text", "marks": [{"type": "code"}], "text": "Secure"}, '
                                        '{"type": "text", "text": " flag must be set to ensure '
                                        'cookies are transmitted exclusively over encrypted HTTPS '
                                        'connections. The "}, {"type": "text", "marks": [{"type": '
                                        '"code"}], "text": "HttpOnly"}, {"type": "text", "text": " '
                                        'flag must be enabled to prevent client side scripts from '
                                        'accessing session tokens via the Document Object Model. '
                                        'Additionally, the "}, {"type": "text", "marks": [{"type": '
                                        '"code"}], "text": "SameSite"}, {"type": "text", "text": " '
                                        'attribute should be configured to "}, {"type": "text", '
                                        '"marks": [{"type": "code"}], "text": "Lax"}, {"type": '
                                        '"text", "text": " or "}, {"type": "text", "marks": '
                                        '[{"type": "code"}], "text": "Strict"}, {"type": "text", '
                                        '"text": " to prevent cookies from being attached '
                                        'automatically to cross origin requests, providing robust '
                                        'protection against cross site request forgery '
                                        'attacks."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resources provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#cookies", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "OWASP Secure '
                                      'Cookie Attributes Cheat Sheet"}]}]}, {"type": "listItem", '
                                      '"content": [{"type": "paragraph", "attrs": {"lead": false}, '
                                      '"content": [{"type": "text", "marks": [{"type": "link", '
                                      '"attrs": {"href": '
                                      '"https://cwe.mitre.org/data/definitions/614.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "CWE-614 Sensitive '
                                      'Cookie in HTTPS Session Without \'Secure\' Attribute"}]}]}, '
                                      '{"type": "listItem", "content": [{"type": "paragraph", '
                                      '"attrs": {"lead": false}, "content": [{"type": "text", '
                                      '"marks": [{"type": "link", "attrs": {"href": '
                                      '"https://cwe.mitre.org/data/definitions/1004.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "CWE-1004 '
                                      'Sensitive Cookie Without \'HttpOnly\' Flag"}]}]}]}, '
                                      '{"type": "paragraph", "attrs": {"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Missing HTTP Strict Transport Security Header',
        'severity': 'LOW',
        'status': 'OPEN',
        'cvss_score': '2.3',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:H/AT:P/PR:N/UI:P/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://redscribe.app',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A02:2025 – Security Misconfiguration']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the assessment of {{ scope }}, assessors '
                                                     'observed that the web server fails to '
                                                     'implement the HTTP Strict Transport Security '
                                                     'header in its HTTP response headers. The '
                                                     'HTTP Strict Transport Security header '
                                                     'informs compliant web browsers that the '
                                                     'application must only be accessed over '
                                                     'encrypted transport connections, instructing '
                                                     'browsers to automatically convert '
                                                     'unencrypted HTTP requests into secure HTTPS '
                                                     'connections before transmitting data across '
                                                     'the network."}]}, {"type": "paragraph", '
                                                     '"attrs": {"lead": false}, "content": '
                                                     '[{"type": "text", "text": "When this '
                                                     'security control is absent, users who enter '
                                                     'plain HTTP web addresses or follow external '
                                                     'links using unencrypted schemes are '
                                                     'vulnerable to transport layer security '
                                                     'downgrade attacks. A malicious adversary '
                                                     'positioned on an intermediate network path '
                                                     'could intercept initial unencrypted '
                                                     'connection requests and perform man in the '
                                                     'middle attacks to strip encryption entirely, '
                                                     'exposing sensitive application traffic to '
                                                     'unauthorized interception."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "The '
                                                     'business impact is categorized as low '
                                                     'because successful exploitation requires an '
                                                     'attacker to occupy an intermediate network '
                                                     'location between the end user and the '
                                                     'application servers. However, in vulnerable '
                                                     'network conditions such as public wireless '
                                                     'access points, the absence of this header '
                                                     'increases the risk of transport layer '
                                                     'downgrade attacks, potentially exposing user '
                                                     'session tokens and transmitted data to '
                                                     'unauthorized network eavesdropping."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Inspection of application HTTP '
                                            'response headers confirmed the absence of the HTTP '
                                            'Strict Transport Security response header across core '
                                            'application endpoints."}]}, {"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "marks": [{"type": "bold"}], "text": "HTTP '
                                            'request:"}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "GET /login HTTP/1.1\\nHost: '
                                            'redscribe.app\\nUser-Agent: Mozilla/5.0 (Windows NT '
                                            '10.0; Win64; x64)\\nAccept: '
                                            'text/html,application/xhtml+xml"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "HTTP response:"}]}, '
                                            '{"type": "codeBlock", "attrs": {"language": null}, '
                                            '"content": [{"type": "text", "text": "HTTP/1.1 200 '
                                            'OK\\nDate: Sun, 20 Sep 2026 00:00:00 GMT\\nServer: '
                                            'nginx\\nContent-Type: text/html; '
                                            'charset=utf-8\\nConnection: '
                                            'keep-alive\\nX-Frame-Options: '
                                            'SAMEORIGIN\\nX-Content-Type-Options: nosniff"}]}, '
                                            '{"type": "paragraph", "attrs": {"lead": false}}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"text": "{{ client_name }} should configure the '
                                        'application web server and reverse proxy infrastructure '
                                        'to inject the Strict-Transport-Security header into all '
                                        'HTTPS responses. The header directive should specify a '
                                        'max-age value of at least one year (31536000 seconds) and '
                                        'include the includeSubDomains directive to ensure '
                                        'security policies apply across all subdomains."}]}, '
                                        '{"type": "paragraph", "attrs": {"lead": false}, '
                                        '"content": [{"type": "text", "text": "Additionally, {{ '
                                        'client_name }} should consider submitting the primary '
                                        'domain to the global browser HTTP Strict Transport '
                                        'Security preload list once operational testing confirms '
                                        'all associated subdomains support secure transport '
                                        'protocols exclusively."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following references provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "OWASP HTTP Strict '
                                      'Transport Security Cheat Sheet"}]}]}, {"type": "listItem", '
                                      '"content": [{"type": "paragraph", "attrs": {"lead": false}, '
                                      '"content": [{"type": "text", "marks": [{"type": "link", '
                                      '"attrs": {"href": '
                                      '"https://datatracker.ietf.org/doc/html/rfc6797", "target": '
                                      '"_blank", "rel": "noopener noreferrer nofollow", "class": '
                                      'null, "title": null}}], "text": "RFC 6797 HTTP Strict '
                                      'Transport Security (HSTS)"}]}]}, {"type": "listItem", '
                                      '"content": [{"type": "paragraph", "attrs": {"lead": false}, '
                                      '"content": [{"type": "text", "marks": [{"type": "link", '
                                      '"attrs": {"href": '
                                      '"https://cwe.mitre.org/data/definitions/523.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "CWE-523 '
                                      'Unprotected Transport of Sensitive Information"}, {"type": '
                                      '"text", "text": " "}]}]}]}, {"type": "paragraph", "attrs": '
                                      '{"lead": false}}]}'}},
    {   'display_id': '',
        'title': 'Missing Rate Limiting on Authentication Endpoints',
        'severity': 'MEDIUM',
        'status': 'OPEN',
        'cvss_score': '6.9',
        'cvss_vector': 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:L/SC:N/SI:N/SA:N',
        'cve_id': '',
        'affects': 'https://redscribe.app/api/v1/auth/login',
        'workflow_status': 'QA_APPROVED',
        'classifications': [['OWASP Top 10 2025', 'A07:2025 – Authentication Failures']],
        'sections': {   'vulnerability-description': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": "During '
                                                     'the security assessment, the login '
                                                     'authentication endpoint on "}, {"type": '
                                                     '"text", "marks": [{"type": "code"}], "text": '
                                                     '"redscribe.app"}, {"type": "text", "text": " '
                                                     'was found to lack rate limiting and request '
                                                     'throttling controls. The application allows '
                                                     'unauthenticated users to submit an unlimited '
                                                     'number of login attempts without triggering '
                                                     'account lockout mechanisms, CAPTCHA '
                                                     'challenges, or IP address blocking."}]}, '
                                                     '{"type": "paragraph", "attrs": {"lead": '
                                                     'false}, "content": [{"type": "text", "text": '
                                                     '"Because the endpoint does not enforce '
                                                     'temporal restrictions on repeated '
                                                     'authentication attempts, an unauthenticated '
                                                     'attacker can launch automated credential '
                                                     'stuffing, brute force, or password spraying '
                                                     'attacks against valid platform '
                                                     'accounts."}]}]}',
                        'business-technical-impact': '{"type": "doc", "content": [{"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Exploitation of this issue allows an '
                                                     'attacker to conduct large scale automated '
                                                     'attacks to compromise legitimate user '
                                                     'accounts, particularly those using weak or '
                                                     'compromised passwords. Successful account '
                                                     'takeover can lead to unauthorized access to '
                                                     'internal resources, tenant data '
                                                     'exfiltration, or secondary attacks against '
                                                     'connected services."}]}, {"type": '
                                                     '"paragraph", "attrs": {"lead": false}, '
                                                     '"content": [{"type": "text", "text": '
                                                     '"Additionally, unrestrained submission of '
                                                     'requests to the authentication service '
                                                     'exposes back-end database infrastructure to '
                                                     'resource exhaustion, potentially impairing '
                                                     'application availability for legitimate '
                                                     'users."}]}]}',
                        'proof-of-concept': '{"type": "doc", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "The absence of rate limiting was '
                                            'verified by issuing automated HTTP POST requests to '
                                            'the login API endpoint using a custom script."}]}, '
                                            '{"type": "bulletList", "content": [{"type": '
                                            '"listItem", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "Formulated a standard authentication '
                                            'request directed to the login endpoint on "}, '
                                            '{"type": "text", "marks": [{"type": "code"}], "text": '
                                            '"redscribe.app"}, {"type": "text", "text": '
                                            '":"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "POST /api/v1/auth/login HTTP/1.1\\nHost: '
                                            'redscribe.app\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"username\\": '
                                            '\\"admin@redscribe.app\\",\\n  \\"password\\": '
                                            '\\"IncorrectPassword123\\"\\n}"}]}, {"type": '
                                            '"bulletList", "content": [{"type": "listItem", '
                                            '"content": [{"type": "paragraph", "attrs": {"lead": '
                                            'false}, "content": [{"type": "text", "text": '
                                            '"Submitted 500 consecutive authentication requests '
                                            'within a 30 second window without varying the source '
                                            'IP address or session details."}]}]}, {"type": '
                                            '"listItem", "content": [{"type": "paragraph", '
                                            '"attrs": {"lead": false}, "content": [{"type": '
                                            '"text", "text": "The server responded to all 500 '
                                            'requests with identical "}, {"type": "text", "marks": '
                                            '[{"type": "code"}], "text": "401 Unauthorized"}, '
                                            '{"type": "text", "text": " responses rather than '
                                            'throttling connections or returning a "}, {"type": '
                                            '"text", "marks": [{"type": "code"}], "text": "429 Too '
                                            'Many Requests"}, {"type": "text", "text": " status '
                                            'code:"}]}]}]}, {"type": "codeBlock", "attrs": '
                                            '{"language": null}, "content": [{"type": "text", '
                                            '"text": "HTTP/1.1 401 Unauthorized\\nContent-Type: '
                                            'application/json\\n\\n{\\n  \\"error\\": \\"Invalid '
                                            'credentials provided.\\"\\n}"}]}, {"type": '
                                            '"paragraph", "attrs": {"lead": false}, "content": '
                                            '[{"type": "text", "text": "No temporary lockout, '
                                            'delay, or additional verification mechanism (such as '
                                            'CAPTCHA) was enforced throughout the test '
                                            'sequence."}]}]}',
                        'remediations': '{"type": "doc", "content": [{"type": "paragraph", '
                                        '"attrs": {"lead": false}, "content": [{"type": "text", '
                                        '"marks": [{"type": "bold"}], "text": "Implement IP and '
                                        'Account Based Rate Limiting:"}, {"type": "text", "text": '
                                        '" Apply rate limiting rules on all authentication '
                                        'endpoints (such as "}, {"type": "text", "marks": '
                                        '[{"type": "code"}], "text": "/api/v1/auth/login"}, '
                                        '{"type": "text", "text": " and password reset routes) to '
                                        'limit the frequency of failed attempts per IP address and '
                                        'per user account."}]}, {"type": "paragraph", "attrs": '
                                        '{"lead": false}, "content": [{"type": "text", "marks": '
                                        '[{"type": "bold"}], "text": "Enforce Progressive Delays '
                                        'and Lockouts:"}, {"type": "text", "text": " Introduce '
                                        'account lockout thresholds or exponential backoff delays '
                                        'after a predefined number of consecutive failed '
                                        'authentication attempts (e.g. 5 failed attempts within 15 '
                                        'minutes)."}]}, {"type": "paragraph", "attrs": {"lead": '
                                        'false}, "content": [{"type": "text", "marks": [{"type": '
                                        '"bold"}], "text": "Deploy CAPTCHA or Adaptive '
                                        'Authentication Controls:"}, {"type": "text", "text": " '
                                        'Trigger risk based verification challenges (such as '
                                        'reCAPTCHA or multi factor prompts) when anomalous login '
                                        'velocity or suspicious request patterns are '
                                        'detected."}]}]}',
                        'references': '{"type": "doc", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "text": "The '
                                      'following resource provide further information about this '
                                      'issue:"}]}, {"type": "bulletList", "content": [{"type": '
                                      '"listItem", "content": [{"type": "paragraph", "attrs": '
                                      '{"lead": false}, "content": [{"type": "text", "marks": '
                                      '[{"type": "link", "attrs": {"href": '
                                      '"https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html", '
                                      '"target": "_blank", "rel": "noopener noreferrer nofollow", '
                                      '"class": null, "title": null}}], "text": "Authentication '
                                      'Cheat Sheet | OWASP"}]}]}]}, {"type": "paragraph", "attrs": '
                                      '{"lead": false}}]}'}}]

created_findings = []
for f in FINDINGS:
    finding, _created = Finding.objects.update_or_create(
        engagement=engagement, title=f["title"],
        defaults={
            "severity": f["severity"], "status": f["status"], "cvss_score": f["cvss_score"],
            "cvss_vector": f["cvss_vector"], "cve_id": f["cve_id"], "affects": f["affects"],
            "workflow_status": f["workflow_status"],
        },
    )
    finding.classifications.clear()
    for taxonomy, value in f["classifications"]:
        tag, _created = ClassificationTag.objects.get_or_create(taxonomy=taxonomy, value=value)
        finding.classifications.add(tag)
    for slug, content_json in f["sections"].items():
        definition = ContentSectionDefinition.objects.get(slug=slug)
        section, _created = FindingSection.objects.get_or_create(finding=finding, definition=definition)
        aad = record_aad("finding", finding.pk, slug)
        section.content_ciphertext = encrypt_bytes(content_json.encode("utf-8"), data_key, associated_data=aad)
        section.save(update_fields=["content_ciphertext"])
    created_findings.append(finding)
print(f"Findings: {len(created_findings)} created/updated")


# ------------------------------------------------------------------ report config (Configure page)

OBSERVATIONS = [   {   'title': 'Information gathering',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the information gathering phase, assessment activities focused on identifying '
                   'exposed information assets, mapping the external application attack surface, '
                   'and discovering metadata that could assist a malicious actor in crafting '
                   'targeted attacks. The primary objective was to evaluate the application '
                   'security posture regarding information leakage through public search engines, '
                   'client side code repositories, and entry point '
                   'mapping."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Public '
                   'Footprint and Path Discovery:"},{"type":"text","text":" Initial passive '
                   'reconnaissance revealed administrative end points and non public directories '
                   'explicitly listed within '
                   '"},{"type":"text","marks":[{"type":"code"}],"text":"robots.txt"},{"type":"text","text":" '
                   'and '
                   '"},{"type":"text","marks":[{"type":"code"}],"text":"sitemap.xml"},{"type":"text","text":" '
                   'files. While intended to prevent search engine indexing, publicly disclosing '
                   'these sensitive paths assists attackers with targeted directory '
                   'discovery."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Information '
                   'Leakage and Asset Enumeration:"},{"type":"text","text":" Examination of client '
                   'side JavaScript assets and publicly downloadable documents uncovered embedded '
                   'developer comments, internal API routes, and static metadata exposing internal '
                   'naming conventions and valid user email '
                   'addresses."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"While '
                   'these individual metadata disclosures and directory mappings do not constitute '
                   'critical security breaches on their own, collectively they reduce the effort '
                   'required for targeted social engineering and focused exploitation against '
                   'organizational infrastructure. No specific vulnerabilities meeting high or '
                   'critical risk thresholds were identified within this specific testing '
                   'category."}]}]}'},
    {   'title': 'Configuration and Deployment Management Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the configuration and deployment management phase, assessment activities '
                   'focused on evaluating the underlying web server setups, application platform '
                   'framework settings, network deployment architecture, and the implementation of '
                   'defensive HTTP security headers. The primary objective was to ensure that the '
                   'hosting environment and framework configurations adhere to industry hardening '
                   'standards, preventing unnecessary technical exposure, downgrade attacks, and '
                   'transport layer '
                   'interception."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Infrastructure '
                   'Fingerprinting and Server Hardening:"},{"type":"text","text":" Active analysis '
                   'of HTTP response headers confirmed that underlying web servers and application '
                   'frameworks consistently disclosed specific software version details through '
                   'response banners such as '
                   '"},{"type":"text","marks":[{"type":"code"}],"text":"Server"},{"type":"text","text":" '
                   'and "},{"type":"text","marks":[{"type":"code"}],"text":"X Powered '
                   'By"},{"type":"text","text":". Disclosing precise version details allows '
                   'potential adversaries to cross reference installed components against public '
                   'vulnerability databases to identify known '
                   'exploits."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Missing '
                   'Security Headers:"},{"type":"text","text":" The application failed to enforce '
                   'strict transport security controls, identified as F009: Missing HTTP Strict '
                   'Transport Security Header (Low). Omitting HSTS headers leaves client '
                   'connections susceptible to man in the middle downgrade attacks, potentially '
                   'allowing attackers to intercept unencrypted HTTP traffic over insecure '
                   'networks."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while the core deployment environment appears stable, hardening the transport '
                   'layer security parameters and suppressing technical banner disclosures will '
                   'significantly reduce the external attack surface across deployed '
                   'infrastructure assets."}]}]}'},
    {   'title': 'Identity Management Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the identity management testing phase, assessment activities focused on '
                   'evaluating the processes, roles, and administrative boundary controls used to '
                   'govern digital identities across the application ecosystem. The primary '
                   'objective was to ensure that identity creation, account provisioning, role '
                   'definitions, and user lifecycle mechanisms prevent unauthorized identity '
                   'creation, privilege escalation, or cross tenant '
                   'exposure."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Identity '
                   'Registration and Role Assignment:"},{"type":"text","text":" Account '
                   'registration workflows properly validated mandatory account details and '
                   'enforced standard baseline permissions upon initial account creation. However, '
                   'identity isolation controls were bypassed downstream during object '
                   'interactions, leading to F002: Insecure Direct Object Reference Leading to PII '
                   'Disclosure (High). By altering user object identifiers within active requests, '
                   'authenticated identities were able to access personally identifiable '
                   'information belonging to other registered '
                   'users."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Privilege '
                   'Segregation and Boundary Enforcement:"},{"type":"text","text":" Analysis of '
                   'role boundaries within multi tenant environments revealed severe access '
                   'control deficiencies, specifically F004: Broken Access Control Allowing '
                   'Horizontal Privilege Escalation in Billing Portal (Medium). The billing portal '
                   'failed to enforce horizontal authorization checks, allowing standard user '
                   'identities to view, manipulate, and interact with billing assets belonging to '
                   'separate organizational '
                   'accounts."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while baseline identity creation and initial role assignments function as '
                   'intended, the application fails to maintain strict identity boundaries across '
                   'object queries and tenant portals, exposing sensitive user data to '
                   'unauthorized identities."}]}]}'},
    {   'title': 'Authentication Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the authentication testing phase, assessment activities focused on evaluating '
                   'the mechanisms used by the application to verify the identity of users '
                   'attempting to access protected resources. The primary objective was to ensure '
                   'that authentication controls resist automated credential guessing, protect '
                   'credential transfer channels, and securely manage identity tokens throughout '
                   'the authentication '
                   'lifecycle."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Authentication '
                   'Safeguards and Anti Automation Controls:"},{"type":"text","text":" The '
                   'application login and password recovery workflows lacked rate limiting '
                   'protections, identified as Missing Rate Limiting on Authentication Endpoints '
                   '(Medium). The absence of request throttling enables malicious actors to '
                   'perform automated brute force and credential stuffing attacks without '
                   'triggering account lockout mechanisms or IP address '
                   'blocking."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Credential '
                   'Reset Flow Integrity:"},{"type":"text","text":" The password reset '
                   'functionality failed to enforce request origin validation, leading to Cross '
                   'Site Request Forgery on Password Reset Form (Medium). This flaw allows '
                   'unauthenticated attackers to trick victim browsers into submitting '
                   'unauthorized password reset requests, potentially leading to account '
                   'compromise."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Token '
                   'Verification and Identity Security:"},{"type":"text","text":" Critical session '
                   'token validation deficiencies were identified within the JSON Web Token '
                   'implementation, specifically F001: Authentication Bypass via Missing JWT '
                   'Signature Validation (Critical). Because the server failed to verify '
                   'cryptographic signatures on incoming tokens, attackers can tamper with token '
                   'claims to bypass authentication entirely and assume arbitrary user '
                   'identities."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while baseline authentication entry points exist, severe vulnerabilities '
                   'within token signature validation and automated attack defenses significantly '
                   'weaken the identity verification controls of the application."}]}]}'},
    {   'title': 'Authorization Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the authorization testing phase, assessment activities focused on verifying '
                   'that the application enforces explicit access controls across all functional '
                   'entry points, data objects, and system workflows. The primary objective was to '
                   'ensure that authenticated users cannot bypass access boundaries to perform '
                   'unauthorized actions, view confidential records belonging to other tenants, or '
                   'escalate their privileges to perform administrative '
                   'operations."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Direct '
                   'Object Access and Data Privacy:"},{"type":"text","text":" The application '
                   'failed to enforce object level authorization checks when handling direct '
                   'parameter references, resulting in F002: Insecure Direct Object Reference '
                   'Leading to PII Disclosure (High). By altering resource identifiers within API '
                   'requests, authenticated users were able to access and exfiltrate personally '
                   'identifiable information associated with other registered '
                   'accounts."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Horizontal '
                   'Access Control and Portal Isolation:"},{"type":"text","text":" Access control '
                   'boundaries within shared functional areas were inadequately restricted, '
                   'specifically F004: Broken Access Control Allowing Horizontal Privilege '
                   'Escalation in Billing Portal (Medium). The billing module lacked strict tenant '
                   'verification, allowing standard users to view, modify, and interact with '
                   'financial assets and invoice records belonging to separate organization '
                   'accounts."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while the application enforces initial role based access controls at top level '
                   'navigation menus, backend endpoints lack robust context aware authorization '
                   'verification, exposing multi tenant boundaries and sensitive user data to '
                   'lateral compromise."}]}]}'},
    {   'title': 'Session Management Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the session management testing phase, assessment activities focused on '
                   'evaluating the mechanisms used to establish, maintain, and terminate secure '
                   'communication states between users and the application. The primary objective '
                   'was to ensure that session identifiers are generated securely, transmitted '
                   'safely over protected channels, and restricted against client side script '
                   'manipulation or transport layer exposure throughout the session '
                   'lifecycle."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Session '
                   'Token Lifecycle and Token Generation:"},{"type":"text","text":" Session '
                   'identifiers were generated using strong pseudo random algorithms, ensuring '
                   'adequate entropy to resist session prediction and brute force attacks. Session '
                   'termination workflows correctly invalidated active tokens on the server side '
                   'upon user logout, preventing token '
                   'reuse."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Cookie '
                   'Attribute Security and Flag Hardening:"},{"type":"text","text":" Application '
                   'session cookies lacked proper defensive security attributes, identified as '
                   'F008: Missing Cookie Flags (Low). Omitting critical attributes such as Secure, '
                   'HttpOnly, or SameSite leaves active session tokens vulnerable to transmission '
                   'over plain text channels, unauthorized access via client side scripts, and '
                   'cross site request forgery '
                   'vectors."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while the core session generation and termination mechanisms adhere to secure '
                   'development practices, failure to enforce strict cookie security attributes '
                   'exposes active user sessions to unnecessary interception and client side '
                   'exploitation risks."}]}]}'},
    {   'title': 'Input Validation Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the input validation testing phase, assessment activities focused on '
                   'evaluating how the application processes, sanitizes, and filters user supplied '
                   'data across all input vectors. The primary objective was to ensure that '
                   'application entry points robustly validate incoming payload structures, '
                   'prevent malicious command interpretation on backend databases, and enforce '
                   'context aware output encoding to safeguard client side browsers against script '
                   'execution."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Backend '
                   'Query Processing and Injection Vulnerabilities:"},{"type":"text","text":" '
                   'Input handling mechanisms failed to safely parameterize user inputs prior to '
                   'database query construction, resulting in F003: SQL Injection (High). By '
                   'injecting structured database control characters into vulnerable parameters, '
                   'an attacker can manipulate underlying SQL statements, leading to unauthorized '
                   'data exfiltration, database schema exposure, and potential host level '
                   'interaction."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Client '
                   'Side Reflection and Script Contexts:"},{"type":"text","text":" Application '
                   'endpoints handling public parameter processing lacked sufficient context aware '
                   'output encoding, leading to F007: Reflected Cross Site Scripting in Search '
                   'Query Parameter (Medium). Unsanitized input echoed back within HTML response '
                   'contexts allows malicious actors to execute arbitrary script content within '
                   'the session context of victim '
                   'browsers."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'the application exhibits systemic deficiencies in handling untrusted user '
                   'input. Failing to enforce strict server side input validation and contextual '
                   'output encoding severely compromises application data integrity and client '
                   'side security boundaries."}]}]}'},
    {   'title': 'Error Handling',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the error handling testing phase, assessment activities focused on evaluating '
                   'how the application behaves when encountering unexpected inputs, system '
                   'exceptions, or malformed requests. The primary objective was to ensure that '
                   'application runtime errors are handled gracefully without revealing sensitive '
                   'backend stack traces, system architecture details, or sensitive database '
                   'information to end '
                   'users."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Exception '
                   'Management and Application Verbosity:"},{"type":"text","text":" Application '
                   'entry points failed to catch runtime exceptions cleanly, resulting in F010: '
                   'Verbose Error Messages (Informational). When provided with unexpected payload '
                   'types or malformed parameter values, the server returned full stack traces and '
                   'database error strings disclosing framework version numbers, file path '
                   'structures, and internal method '
                   'names."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Informational '
                   'Disclosure Risks:"},{"type":"text","text":" Disclosing internal stack traces '
                   'provides malicious actors with critical insights into underlying code '
                   'architecture and component dependencies. While this information leakage does '
                   'not allow direct system compromise on its own, it significantly reduces the '
                   'reconnaissance effort required to identify application flaws and map out '
                   'viable attack '
                   'paths."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while core business functionalities continue operating during standard '
                   'workflows, the absence of customized generic error pages leaves the '
                   'application open to information gathering through deliberate exception '
                   'triggering."}]}]}'},
    {   'title': 'Weak Cryptography',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the weak cryptography testing phase, assessment activities focused on '
                   'evaluating the cryptographic mechanisms implemented to protect data in transit '
                   'and data at rest. The primary objective was to ensure that strong encryption '
                   'algorithms, robust cipher suites, safe key management practices, and proper '
                   'digital signature schemes are used to maintain data confidentiality and '
                   'integrity across all application '
                   'layers."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Cryptographic '
                   'Signature Verification:"},{"type":"text","text":" Severe deficiencies were '
                   'identified in the cryptographic handling of JSON Web Tokens, specifically '
                   'F001: Authentication Bypass via Missing JWT Signature Validation (Critical). '
                   'The application failed to cryptographically verify token signatures upon '
                   'receiving requests, allowing arbitrary modification of token headers and '
                   'payloads without invalidating the '
                   'session."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Transport '
                   'Layer Encryption Standards:"},{"type":"text","text":" Assessment of TLS and '
                   'transport protocol setups confirmed that modern cipher suites were supported. '
                   'However, transport security enforcement was compromised due to F009: Missing '
                   'HTTP Strict Transport Security Header (Low), which allows unencrypted HTTP '
                   'connections to persist and exposes data transmission to potential interception '
                   'over insecure network '
                   'channels."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Algorithm '
                   'and Key Hardening:"},{"type":"text","text":" Beyond the JWT signature '
                   'validation failure, no deprecated symmetric encryption algorithms or weak hash '
                   'functions were observed within visible application data '
                   'flows."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while transport layer configurations utilize modern protocols, the failure to '
                   'enforce cryptographic signature verification on identity tokens represents a '
                   'severe failure in the application cryptographic architecture."}]}]}'},
    {   'title': 'Business Logic Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the business logic testing phase, assessment activities focused on evaluating '
                   'the application operational workflows, multi step processes, and functional '
                   'business rules. The primary objective was to ensure that the application '
                   'enforces intended procedural sequence, prevents state manipulation, and '
                   'resists misuse where malicious actors might exploit legitimate functionalities '
                   'to bypass business '
                   'constraints."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Workflow '
                   'Integrity and Order Execution:"},{"type":"text","text":" Primary business '
                   'workflows, including registration sequences and transaction pipelines, '
                   'correctly maintained state integrity across multi step processes. Users were '
                   'unable to skip prerequisite steps or force the application into undefined '
                   'intermediate states to bypass validation '
                   'rules."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Process '
                   'Flaws and Access Boundaries:"},{"type":"text","text":" Functional controls '
                   'within specialized portals failed to properly validate authorization context '
                   'against business assets, resulting in F004: Broken Access Control Allowing '
                   'Horizontal Privilege Escalation in Billing Portal (Medium). This logic flaw '
                   'allows authenticated tenants to interact with and modify billing assets '
                   'belonging to other accounts, violating fundamental business separation '
                   'controls."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Input '
                   'Limits and Resource Constraints:"},{"type":"text","text":" The application '
                   'enforced basic validation checks on transaction parameters and numerical '
                   'quantities, preventing common logic abuses such as negative pricing or integer '
                   'overflow conditions during standard '
                   'workflows."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while procedural step sequences and input boundary limits operate as intended, '
                   'business logic enforcement falls short in isolating organizational boundaries '
                   'within shared portal environments."}]}]}'},
    {   'title': 'Client-side Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"During '
                   'the client side testing phase, assessment activities focused on evaluating the '
                   'execution safety of code running within client web browsers, cross origin '
                   'resource sharing configurations, document object model interactions, and local '
                   'data storage mechanisms. The primary objective was to ensure that client side '
                   'components safely handle untrusted data, restrict malicious script execution, '
                   'and prevent unauthorized cross origin '
                   'communication."}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Key '
                   'technical observations made during this phase '
                   'include:"}]},{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Script '
                   'Reflection and Context Rendering:"},{"type":"text","text":" Client side '
                   'rendering logic failed to safely encode dynamic data returned from application '
                   'parameters, leading to F007: Reflected Cross Site Scripting in Search Query '
                   'Parameter (Medium). When malicious script payloads are embedded within query '
                   'strings, the browser executes the script within the user origin context, '
                   'permitting session hijacking and DOM '
                   'manipulation."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Client '
                   'Side Data Storage and Session Persistence:"},{"type":"text","text":" Local web '
                   'storage objects and browser caches were inspected for sensitive information '
                   'remnants. While session state tokens were primarily handled via HTTP cookies, '
                   'these storage vectors were vulnerable to interception due to F008: Missing '
                   'Cookie Flags (Low), as cookies lacked flags necessary to prevent script '
                   'readability and plain text '
                   'transmission."}]}]},{"type":"listItem","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","marks":[{"type":"bold"}],"text":"Cross '
                   'Origin and Resource Isolation Controls:"},{"type":"text","text":" Evaluation '
                   'of resource sharing policies confirmed that cross origin requests were '
                   'restricted to approved domains without permissive wildcard configurations. '
                   'However, client side assets contained exposed developer comments and internal '
                   'route definitions that assisted with application mapping during earlier '
                   'assessment '
                   'phases."}]}]}]},{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Overall, '
                   'while cross origin restrictions and local storage configurations align with '
                   'general baseline standards, client side parameter handling lacks sufficient '
                   'output encoding, leaving users vulnerable to script execution attacks within '
                   'their browsers."}]}]}'}]
TESTING_PHASES = [   {   'title': 'Scope and Target Identification',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                   'testing methodology section outlines the operational framework, technical '
                   'approach, and execution boundaries governed during the targeted web '
                   'application penetration test. The assessment followed a structured, risk based '
                   'approach aligned with CREST guidelines and the OWASP Web Security Testing '
                   'Guide (WSTG v4.2). Testing activities combined automated baseline '
                   'reconnaissance with safe, controlled manual exploitation to evaluate the '
                   'security posture of the target web application."}]}]}'},
    {   'title': 'Scope and Target Identification',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Assessment '
                   'activities were strictly restricted to the authorized target application '
                   'environments and supporting endpoints. Testing was performed against the '
                   'designated web application targets, associated RESTful API routes, and user '
                   'authentication workflows. Out of scope infrastructure, including third party '
                   'identity providers, external payment gateways, and underlying cloud provider '
                   'physical hosting layers, were explicitly excluded from direct exploitation '
                   'activities to ensure zero operational disruption to live services."}]}]}'},
    {   'title': 'Pre Engagement and Reconnaissance',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                   'initial phase established operational parameters, confirmed source testing IP '
                   'addresses, and validated active user accounts provided for testing. '
                   'Reconnaissance activities involved passive footprinting and active target '
                   'mapping to establish the external application surface area. Technical efforts '
                   'focused on identifying exposed web server technologies, mapping client side '
                   'assets, discovering hidden API routes, and identifying active entry points '
                   'without impacting service availability."}]}]}'},
    {   'title': 'Threat Modeling and Vulnerability Analysis',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Following '
                   'surface mapping, the target application was evaluated against common attack '
                   'vectors and structural vulnerabilities. Automated vulnerability scanners were '
                   'utilized solely for initial baseline discovery and configuration auditing. All '
                   'identified anomalies were subsequently reviewed and manually validated by '
                   'testing consultants to eliminate false positives. Threat modeling focused on '
                   'identifying high risk transaction paths, such as authentication workflows, '
                   'session state transitions, data input parameters, and multi tenant role '
                   'boundaries."}]}]}'},
    {   'title': 'Manual Exploitation and Deep Testing',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Manual '
                   'exploitation techniques were applied to validate suspected vulnerabilities and '
                   'assess the real world security impact on business assets. Testing activities '
                   'focused on evaluating input validation controls, parameter handling, session '
                   'integrity, cryptographic signature enforcement, and access control boundaries '
                   'across user roles. Exploitation attempts were executed safely and '
                   'proportionately to demonstrate risk without corrupting database integrity, '
                   'exposing sensitive tenant data, or causing application downtime."}]}]}'},
    {   'title': 'Post Exploitation and Impact Assessment',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"Once '
                   'security flaws were successfully demonstrated, technical analysis was '
                   'conducted to evaluate the potential impact of a full compromise. This phase '
                   'determined whether initial access, such as an authentication bypass or input '
                   'injection, could lead to horizontal privilege escalation, sensitive data '
                   'exfiltration, or underlying system access. Findings were mapped against '
                   'business impact metrics to derive accurate severity ratings prior to client '
                   'reporting."}]}]}'},
    {   'title': 'Reporting and Remediation Guidance',
        'content': '{"type":"doc","content":[{"type":"paragraph","attrs":{"lead":false},"content":[{"type":"text","text":"The '
                   'final phase involved synthesizing technical evidence, reproduction steps, and '
                   'qualitative observations into an actionable report. Each identified finding '
                   'was assigned a risk rating based on likelihood and impact metrics. Tailored '
                   'remediation recommendations were established for each vulnerability, '
                   'prioritizing high risk systemic issues to assist organizational development '
                   'teams with effective security hardening and patch implementation."}]}]}'}]

report_config, _created = ReportConfig.objects.get_or_create(
    engagement=engagement, is_template=False, defaults={"name": "Draft"},
)
report_config.profile = profile
report_config.content = {
    "cover": {
        "title": "SAMPLE Web Application Penetration Test Report",
        "classification_label": "AI GENERATED REPORT CONTENT",
    },
    "dynamic": BLOCK_DEFAULTS,
    "toggles": {"page_break_per_finding": False},
    "findings": {
        "statuses": None,
        "severities": None,
        "included_ids": [str(finding.pk) for finding in created_findings],
    },
    "breakdown": {
        "intro": json.dumps({"type": "doc", "content": [
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Findings by severity"}]},
            {"type": "paragraph", "attrs": {"lead": False}},
        ]}),
        "notes": json.dumps({"type": "doc", "content": [
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Findings overview"}]},
            {"type": "paragraph", "attrs": {"lead": False}},
        ]}),
        "enabled": True,
        "statuses": ["OPEN", "CLOSED"],
        "severities": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
        "show_chart": True,
        "show_table": True,
    },
    "observations": OBSERVATIONS,
    "testing_phases": TESTING_PHASES,
    "document_control": {
        "notes": json.dumps({"type": "doc", "content": [{"type": "paragraph", "attrs": {"lead": False}}]}),
    },
}
report_config.save()
print(f"Report config: {len(OBSERVATIONS)} observations, {len(TESTING_PHASES)} testing phases")

print()
print("Done. Open the engagement's Report tab, Configure, pick the")
print("'Web Application' profile if it isn't already selected, and export a PDF.")