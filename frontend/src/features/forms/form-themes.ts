/** Theme groupings for profile edit wizards (3–5 themes instead of 20 linear steps). */

export interface FormTheme {
  key: string
  label: string
  sectionKeys: string[]
}

export const organizationFormThemes: FormTheme[] = [
  {
    key: 'identity',
    label: 'Identity & Overview',
    sectionKeys: ['identity', 'company_overview'],
  },
  {
    key: 'operations',
    label: 'Territories & Delivery',
    sectionKeys: ['operating_territories', 'delivery_capability'],
  },
  {
    key: 'capabilities',
    label: 'Capabilities & Compliance',
    sectionKeys: ['certifications_compliance', 'technology_expertise'],
  },
  {
    key: 'references_and_constraints',
    label: 'References & Constraints',
    sectionKeys: ['references', 'macro_deal_constraints'],
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
    label: 'ICP & Buyer Personas',
    sectionKeys: ['icp', 'buyer_personas', 'use_cases', 'customer_triggers'],
  },
  {
    key: 'commercials_and_diffs',
    label: 'Pricing & Differentiation',
    sectionKeys: [
      'pricing',
      'competitors',
      'differentiators',
      'keywords',
      'signals',
    ],
  },
  {
    key: 'delivery',
    label: 'Delivery & Proof',
    sectionKeys: ['implementation', 'integrations', 'customer_success_stories'],
  },
  {
    key: 'compliance_and_exclusions',
    label: 'Compliance & Exclusions',
    sectionKeys: ['compliance_restrictions', 'exclusion_rules'],
  },
]

export const strategyFormThemes: FormTheme[] = [
  {
    key: 'overview_and_targets',
    label: 'Overview & Targets',
    sectionKeys: ['overview', 'run_targets'],
  },
  {
    key: 'target_decision_makers',
    label: 'Decision Makers',
    sectionKeys: ['target_decision_makers'],
  },
  {
    key: 'target_company_profile',
    label: 'Company Profile',
    sectionKeys: [
      'target_company_profile',
      'priority_industries',
      'priority_geographies',
      'company_size',
    ],
  },
  {
    key: 'discovery_signals_and_sources',
    label: 'Discovery & Sources',
    sectionKeys: [
      'buying_signals',
      'prospecting_strategy',
      'competitor_targeting',
    ],
  },
  {
    key: 'qualification_and_exclusions',
    label: 'Qualification & Exclusions',
    sectionKeys: [
      'qualification_criteria',
      'prioritization_rules',
      'exclusion_rules',
      'experiments',
      'success_metrics',
    ],
  },
]
