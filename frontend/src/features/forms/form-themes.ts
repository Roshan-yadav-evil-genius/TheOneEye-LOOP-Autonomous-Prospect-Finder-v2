/** Theme groupings for profile edit wizards (3–5 themes instead of 20 linear steps). */

export interface FormTheme {
  key: string
  label: string
  sectionKeys: string[]
}

export const organizationFormThemes: FormTheme[] = [
  {
    key: 'identity',
    label: 'Identity',
    sectionKeys: ['identity', 'company_overview', 'industry', 'business_model', 'company_size'],
  },
  {
    key: 'markets',
    label: 'Markets & ICP',
    sectionKeys: [
      'target_markets',
      'existing_customers',
      'customer_segments',
      'brand_positioning',
      'unique_strengths',
    ],
  },
  {
    key: 'gtm',
    label: 'GTM',
    sectionKeys: [
      'competitive_landscape',
      'sales_goals',
      'partnership_strategy',
      'sales_process',
      'pricing_position',
      'deal_constraints',
    ],
  },
  {
    key: 'delivery',
    label: 'Delivery',
    sectionKeys: [
      'delivery_capability',
      'technology_expertise',
      'case_studies',
      'references',
    ],
  },
  {
    key: 'compliance',
    label: 'Compliance',
    sectionKeys: ['certifications_compliance'],
  },
]

export const productFormThemes: FormTheme[] = [
  {
    key: 'identity',
    label: 'Identity',
    sectionKeys: ['identity', 'product_overview', 'problem_solved', 'value_proposition'],
  },
  {
    key: 'icp',
    label: 'ICP',
    sectionKeys: ['icp', 'buyer_personas', 'use_cases', 'customer_triggers', 'exclusion rules'],
  },
  {
    key: 'gtm',
    label: 'GTM',
    sectionKeys: [
      'competitors',
      'differentiators',
      'pricing',
      'keywords',
      'signals',
    ],
  },
  {
    key: 'delivery',
    label: 'Delivery',
    sectionKeys: ['implementation', 'integrations', 'customer_success_stories'],
  },
  {
    key: 'compliance',
    label: 'Compliance',
    sectionKeys: ['compliance_restrictions'],
  },
]

export const strategyFormThemes: FormTheme[] = [
  {
    key: 'identity',
    label: 'Identity',
    sectionKeys: ['overview', 'run_targets'],
  },
  {
    key: 'icp',
    label: 'ICP',
    sectionKeys: [
      'target_company_profile',
      'target_decision_makers',
      'priority_industries',
      'priority_geographies',
      'company_size',
    ],
  },
  {
    key: 'gtm',
    label: 'GTM',
    sectionKeys: [
      'buying_signals',
      'prospecting_strategy',
      'outreach_strategy',
      'messaging_hypotheses',
      'qualification_criteria',
      'prioritization_rules',
      'competitor_targeting',
    ],
  },
  {
    key: 'guardrails',
    label: 'Guardrails',
    sectionKeys: ['blacklist_criteria', 'exclusion_rules'],
  },
  {
    key: 'learning',
    label: 'Learning',
    sectionKeys: ['experiments', 'success_metrics', 'lessons_learned', 'best_practices'],
  },
]
