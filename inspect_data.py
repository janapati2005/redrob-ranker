import json

with open('data/sample_candidates.json') as f:
    data = json.load(f)

c = data[30]  # CAND_0000031 - our best candidate
print('Candidate:', c['candidate_id'])

print('\n=== FIELDS WE USE ===')
print('skills:', len(c['skills']), 'skills')
print('career_history:', len(c['career_history']), 'jobs')

print('\n=== FIELDS WE ARE IGNORING ===')

print('\n1. EDUCATION:')
for edu in c['education']:
    degree = edu.get('degree', '')
    field = edu.get('field_of_study', '')
    inst = edu.get('institution', '')
    tier = edu.get('tier', 'unknown')
    grade = edu.get('grade', 'none')
    print(f'   {degree} in {field} from {inst}')
    print(f'   tier: {tier} | grade: {grade}')

print('\n2. CERTIFICATIONS:')
for cert in c.get('certifications', []):
    print(f'   {cert["name"]} from {cert["issuer"]} ({cert["year"]})')

print('\n3. LANGUAGES:')
for lang in c.get('languages', []):
    print(f'   {lang["language"]} - {lang["proficiency"]}')

print('\n4. REDROB SIGNALS WE IGNORE:')
s = c['redrob_signals']
print(f'   profile_completeness_score : {s["profile_completeness_score"]}')
print(f'   applications_submitted_30d : {s["applications_submitted_30d"]}')
print(f'   avg_response_time_hours    : {s["avg_response_time_hours"]}')
print(f'   connection_count           : {s["connection_count"]}')
print(f'   endorsements_received      : {s["endorsements_received"]}')
print(f'   search_appearance_30d      : {s["search_appearance_30d"]}')
print(f'   saved_by_recruiters_30d    : {s["saved_by_recruiters_30d"]}')
print(f'   interview_completion_rate  : {s["interview_completion_rate"]}')
print(f'   offer_acceptance_rate      : {s["offer_acceptance_rate"]}')
print(f'   preferred_work_mode        : {s["preferred_work_mode"]}')
print(f'   expected_salary_inr_lpa    : {s["expected_salary_range_inr_lpa"]}')
print(f'   linkedin_connected         : {s["linkedin_connected"]}')

print('\n5. CAREER DESCRIPTION (first job):')
print('  ', c['career_history'][0]['description'][:400])

print('\n6. CURRENT COMPANY SIZE:')
print('  ', c['profile']['current_company_size'])

print('\n7. EDUCATION TIER ACROSS ALL 50 CANDIDATES:')
from collections import Counter
tiers = []
for candidate in data:
    for edu in candidate.get('education', []):
        tiers.append(edu.get('tier', 'unknown'))
print('   Distribution:', Counter(tiers))