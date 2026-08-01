export interface FormSection {
  key: string
  title: string
  help: string
}

export const organizationSections: FormSection[] = [
  ['identity', 'Organization identity', 'Name, website, primary contact email, logo.'],
  ['company_overview', 'Company overview', 'Description, mission, founding year, headquarters.'],
  ['operating_territories', 'Operating territories', 'Countries and regions where seller operates and supports clients.'],
  ['delivery_capability', 'Delivery capability', 'Geography, languages, support, implementation capacity.'],
  ['certifications_compliance', 'Certifications & compliance', 'Certifications, frameworks, data residency.'],
  ['technology_expertise', 'Technology expertise', 'Cloud, languages, platforms, and tools.'],
  ['references', 'References', 'Logo clients, websites, and reference industries.'],
  ['macro_deal_constraints', 'Macro deal constraints', 'Minimum contract value, geographic limits, deal breakers.'],
].map(([key, title, help]) => ({ key, title, help }))

export const productSections: FormSection[] = [
  ['identity', 'Product identity', 'Product/service name and kind.'],
  ['product_overview', 'Product overview', 'One-sentence summary and offering scope.'],
  ['problem_solved', 'Problem solved', 'Primary pain, secondary pains, cost of inaction.'],
  ['value_proposition', 'Value proposition', 'Primary value and measurable outcomes.'],
  ['icp', 'Ideal customer profile', 'Industry, customer segments, size, geography, type, maturity.'],
  ['buyer_personas', 'Buyer personas', 'Primary titles, buyers, evaluators, seniority.'],
  ['use_cases', 'Use cases', 'Trigger, scenario, and expected outcome.'],
  ['customer_triggers', 'Customer triggers', 'Events indicating current need.'],
  ['pricing', 'Pricing', 'Model, price band, range, minimum, cycle, engagement.'],
  ['competitors', 'Competitors', 'Direct and indirect alternatives.'],
  ['differentiators', 'Differentiators', 'Why customers choose this offering.'],
  ['implementation', 'Implementation', 'Setup, onboarding, requirements, customer resources.'],
  ['integrations', 'Integrations', 'Must-have, nice-to-have, ecosystems.'],
  ['customer_success_stories', 'Customer success stories', 'At least five reference companies.'],
  ['compliance_restrictions', 'Compliance / restrictions', 'Regions, certifications, legal and technical limits.'],
  ['keywords', 'Keywords', 'Problem, category, technology, and role terms.'],
  ['signals', 'Signals', 'Public indicators of active need.'],
  ['exclusion_rules', 'Exclusion rules', 'Product-level exclusion rules.'],
].map(([key, title, help]) => ({ key, title, help }))

export const strategySections: FormSection[] = [
  ['overview', 'Sales strategy overview', 'Name, description, and target narrative.'],
  ['run_targets', 'Run targets', 'Target company count and default contacts per company.'],
  ['target_decision_makers', 'Target decision makers', 'Primary/secondary titles, seniority levels, department functions.'],
  ['target_company_profile', 'Target company profile', 'Types, characteristics, examples, keywords, pains.'],
  ['priority_industries', 'Priority industries', 'Primary, secondary, and deprioritized industries.'],
  ['priority_geographies', 'Priority geographies', 'Countries, regions, cities, remote and exclusions.'],
  ['company_size', 'Company size', 'Employee/revenue bands and segment tags.'],
  ['buying_signals', 'Buying signals', 'Selected and custom current signals.'],
  ['prospecting_strategy', 'Prospecting strategy', 'Sources, excluded domain types, and source-specific hints.'],
  ['competitor_targeting', 'Competitor targeting', 'Incumbents, switch triggers, exceptions.'],
  ['qualification_criteria', 'Qualification criteria', 'Must-have, nice-to-have, confidence.'],
  ['prioritization_rules', 'Prioritization rules', 'Ordering and tie-break rules.'],
  ['exclusion_rules', 'Exclusion rules', 'Rules, named companies, domains, industries, and regions to block.'],
  ['experiments', 'Experiments', 'Hypothesis, variant, success criteria, notes.'],
  ['success_metrics', 'Success metrics', 'Operator-defined run targets.'],
].map(([key, title, help]) => ({ key, title, help }))

export const organizationTemplate: Record<string, unknown> = {
  company_overview: { description: '', mission: '', founded_year: null, headquarters: '' },
  operating_territories: { countries: [], regions: [] },
  delivery_capability: { geography: [], languages: [], support_hours: '', implementation_capacity: '' },
  certifications_compliance: { certifications: [], frameworks: [], data_residency: '' },
  technology_expertise: { cloud: [], languages: [], platforms: [], tools: [] },
  references: { clients: [{ name: '', website: '' }], industries: [] },
  macro_deal_constraints: { min_contract_value: '', geographic_limits: [], other: '' },
}

export const productTemplate: Record<string, unknown> = {
  product_overview: { summary: '', offering_scope: '' },
  problem_solved: { primary: '', secondary: [], cost_of_inaction: '' },
  value_proposition: { primary: '', outcomes: [] },
  icp: {
    customer_segments: { primary: [], secondary: [], avoid: [] },
    industries: { primary: [], secondary: [], avoid: [] },
    company_size: { employees_min: null, employees_max: null, revenue_min: null, revenue_max: null },
    geography: { countries: [], regions: [], exclude_countries: [] },
    company_types: [],
    maturity: [],
  },
  buyer_personas: { primary_titles: [], economic_buyer: '', technical_evaluator: '', seniority: [] },
  use_cases: [{ name: '', trigger: '', outcome: '' }],
  customer_triggers: [],
  pricing: { model: '', price_band: '', typical_range: '', min_deal_size: '', sales_cycle: '', engagement_model: '' },
  competitors: [{ name: '', website: '', type: 'direct' }],
  differentiators: [],
  implementation: { setup_effort: '', onboarding_duration: '', technical_requirements: [], customer_resources: [] },
  integrations: { must_have: [], nice_to_have: [], ecosystems: [] },
  customer_success_stories: [{ name: '', website: '', industry: '', why_they_bought: '', outcome: '' }],
  compliance_restrictions: { regions_blocked: [], certifications: [], legal_notes: '', technical_limits: [] },
  keywords: [],
  signals: [],
  exclusion_rules: { rules: [], free_text: '' },
}

export const strategyTemplate: Record<string, unknown> = {
  overview: { thumbnail_url: '', name: '', description: '', target_companies_narrative: '' },
  run_targets: { target_companies: 0, contacts_per_company_default: 0 },
  target_decision_makers: {
    primary_titles: [],
    secondary_titles: [],
    seniority_levels: [],
    department_functions: [],
    seniority_order: [],
    contact_buying_signals: [],
  },
  target_company_profile: { company_types: [], characteristics: [], similar_companies: [], keywords: [], problems_they_should_have: [] },
  priority_industries: { primary: [], secondary: [], deprioritized: [] },
  priority_geographies: { countries: [], regions: [], cities: [], remote_only: false, exclude_countries: [] },
  company_size: { employees_min: null, employees_max: null, revenue_min: null, revenue_max: null, segments: [] },
  buying_signals: { selected: [], custom: [] },
  prospecting_strategy: { sources: [], excluded_domain_types: [], source_hints: {} },
  competitor_targeting: { incumbents_to_target: [], switch_triggers: [], avoid_unless_scaling: [] },
  qualification_criteria: { must_have: [], nice_to_have: [], min_confidence_hint: null },
  prioritization_rules: { rules: [] },
  exclusion_rules: { rules: [], companies: [], domains: [], industries: [], regions: [] },
  experiments: [{ hypothesis: '', variant: '', success_criteria: '', notes: '' }],
  success_metrics: { targets: [] },
}
