export type FieldKind =
  | 'text'
  | 'textarea'
  | 'number'
  | 'boolean'
  | 'string-list'
  | 'select'
  | 'multi-select'
  | 'object-list'
  | 'file'

export interface FormField {
  path: string
  label: string
  kind: FieldKind
  help?: string
  options?: string[]
  required?: boolean
  itemFields?: FormField[]
}

export interface FormSectionDefinition {
  key: string
  title: string
  help: string
  fields: FormField[]
}

const stringList = (path: string, label: string, help?: string): FormField => ({
  path,
  label,
  kind: 'string-list',
  help,
})

const text = (path: string, label: string, help?: string, required = false): FormField => ({
  path,
  label,
  kind: 'text',
  help,
  required,
})

const file = (path: string, label: string, help?: string): FormField => ({
  path,
  label,
  kind: 'file',
  help,
})

const area = (path: string, label: string, help?: string, required = false): FormField => ({
  path,
  label,
  kind: 'textarea',
  help,
  required,
})

const num = (path: string, label: string, help?: string): FormField => ({
  path,
  label,
  kind: 'number',
  help,
})

export const organizationFormSections: FormSectionDefinition[] = [
  {
    key: 'identity',
    title: 'Organization identity',
    help: 'Basic record fields stored on Organization.',
    fields: [
      file('thumbnail_url', 'Thumbnail / Logo', 'Upload an image for the organization'),
      text('name', 'Organization name', 'Legal or brand name', true),
      text('website', 'Website', 'Canonical company website', true),
      text('primary_contact_email', 'Primary contact email', 'Optional notification contact'),
    ],
  },
  {
    key: 'company_overview',
    title: 'Company overview',
    help: 'What the company does and its mission.',
    fields: [
      area('description', 'What the company does', '2–5 sentences', true),
      area('mission', 'Mission or vision', '1–2 sentences on purpose or long-term goal', true),
      num('founded_year', 'Year founded', 'Four-digit year the company was founded'),
      text('headquarters', 'Headquarters location', 'City and country, e.g. San Francisco, US'),
    ],
  },
  {
    key: 'operating_territories',
    title: 'Operating territories',
    help: 'Countries and regions where seller can legally and logistically operate and support clients.',
    fields: [
      stringList('countries', 'Countries', 'Countries you actively operate in; one per line'),
      stringList('regions', 'Regions', 'Macro regions served, e.g. North America or EMEA; one per line'),
    ],
  },
  {
    key: 'delivery_capability',
    title: 'Delivery capability',
    help: 'Geographic coverage and implementation capacity.',
    fields: [
      stringList('geography', 'Delivery geography', 'Countries or regions where you can implement and support; one per line'),
      stringList('languages', 'Languages supported', 'Languages available for sales and support; one per line'),
      text('support_hours', 'Support hours / time zones', 'Coverage window and primary time zones, e.g. 9–5 ET'),
      area('implementation_capacity', 'Implementation capacity', 'Team size, backlog, or limits on simultaneous projects'),
    ],
  },
  {
    key: 'certifications_compliance',
    title: 'Certifications & compliance',
    help: 'Certifications and frameworks customers require.',
    fields: [
      stringList('certifications', 'Certifications', 'Held certifications, e.g. ISO 27001 or SOC 2; one per line'),
      stringList('frameworks', 'Compliance frameworks', 'Frameworks you align with, e.g. GDPR or HIPAA; one per line'),
      text('data_residency', 'Data residency / security commitments', 'Where customer data is stored and key security promises'),
    ],
  },
  {
    key: 'technology_expertise',
    title: 'Technology expertise',
    help: 'Company-wide technical strengths.',
    fields: [
      stringList('cloud', 'Cloud providers', 'Cloud platforms you deploy on, e.g. AWS or Azure; one per line'),
      stringList('languages', 'Languages / frameworks', 'Development languages and frameworks you excel in; one per line'),
      stringList('platforms', 'Platforms', 'CRM, ERP, or vertical platforms you specialize on; one per line'),
      stringList('tools', 'Tools', 'Delivery or internal tools your team is expert with; one per line'),
    ],
  },
  {
    key: 'references',
    title: 'References',
    help: 'Well-known clients and reference industries.',
    fields: [
      {
        path: 'clients',
        label: 'Clients',
        kind: 'object-list',
        help: 'Logo or name-drop clients prospects may recognize.',
        itemFields: [
          text('name', 'Name', 'Client company name'),
          text('website', 'Website', 'Canonical client website URL'),
        ],
      },
      stringList('industries', 'Reference industries', 'Industries where you have strong references; one per line'),
    ],
  },
  {
    key: 'macro_deal_constraints',
    title: 'Macro deal constraints',
    help: 'Hard rules for business fit and deal breakers.',
    fields: [
      text('min_contract_value', 'Minimum contract value', 'Smallest deal size you will pursue, in your currency'),
      stringList('geographic_limits', 'Geographic limitations', 'Regions or countries you cannot serve; one per line'),
      area('other', 'Other deal breakers', 'Any other hard rules that disqualify an opportunity'),
    ],
  },
]

export const productFormSections: FormSectionDefinition[] = [
  {
    key: 'identity',
    title: 'Product identity',
    help: 'Product/service name and kind.',
    fields: [
      file('thumbnail_url', 'Thumbnail / Logo', 'Upload an image for the product or service'),
      text('name', 'Name', 'Product or service name as prospects would recognize it', true),
      {
        path: 'kind',
        label: 'Kind',
        kind: 'select',
        help: 'Whether this offering is a product or a service.',
        options: ['product', 'service'],
        required: true,
      },
    ],
  },
  {
    key: 'product_overview',
    title: 'Product overview',
    help: 'What the offering does.',
    fields: [
      area('summary', 'One-sentence summary', 'Single sentence describing what the offering does', true),
      area('offering_scope', 'Offering scope', 'What is included and excluded from this offering'),
    ],
  },
  {
    key: 'problem_solved',
    title: 'Problem solved',
    help: 'Business problem or pain point.',
    fields: [
      area('primary', 'Primary problem', 'Main business pain this offering solves', true),
      stringList('secondary', 'Secondary pains', 'Related problems buyers also feel; one per line'),
      area('cost_of_inaction', 'Cost of inaction', 'What happens if the buyer does nothing'),
    ],
  },
  {
    key: 'value_proposition',
    title: 'Value proposition',
    help: 'Why it is better than alternatives.',
    fields: [
      area('primary', 'Primary value proposition', 'Core reason to buy vs status quo or rivals', true),
      stringList('outcomes', 'Top outcomes', 'Measurable results customers achieve; one per line'),
    ],
  },
  {
    key: 'icp',
    title: 'Ideal customer profile',
    help: 'General fit profile for this offering.',
    fields: [
      stringList('customer_segments.primary', 'Primary customer segments', 'Main ICP segments; one per line'),
      stringList('customer_segments.secondary', 'Secondary customer segments', 'Additional accepted segments; one per line'),
      stringList('customer_segments.avoid', 'Avoid customer segments', 'Segments to decline or deprioritize; one per line'),
      stringList('industries.primary', 'Primary industries', 'Best-fit industries for this offering; one per line'),
      stringList('industries.secondary', 'Secondary industries', 'Acceptable but lower-priority industries; one per line'),
      stringList('industries.avoid', 'Industries to avoid', 'Industries that are a poor fit; one per line'),
      num('company_size.employees_min', 'Employees min', 'Minimum employee count for a good-fit company'),
      num('company_size.employees_max', 'Employees max', 'Maximum employee count for a good-fit company'),
      num('company_size.revenue_min', 'Revenue min', 'Minimum annual revenue for a good-fit company'),
      num('company_size.revenue_max', 'Revenue max', 'Maximum annual revenue for a good-fit company'),
      stringList('geography.countries', 'Countries', 'Countries where prospects should be based; one per line'),
      stringList('geography.regions', 'Regions', 'Macro regions to include; one per line'),
      stringList('geography.exclude_countries', 'Excluded countries', 'Countries to exclude from targeting; one per line'),
      stringList('company_types', 'Company types', 'Firm types that fit, e.g. SaaS or agency; one per line'),
      stringList('maturity', 'Maturity', 'Company maturity signals, e.g. Series B or public; one per line'),
    ],
  },
  {
    key: 'buyer_personas',
    title: 'Buyer personas',
    help: 'Who usually buys or champions the deal.',
    fields: [
      stringList('primary_titles', 'Primary buyer titles', 'Job titles that usually own the purchase; one per line'),
      text('economic_buyer', 'Economic buyer', 'Role that signs the contract or controls budget'),
      text('technical_evaluator', 'Technical evaluator', 'Role that assesses technical fit'),
      stringList('seniority', 'Seniority', 'Typical seniority levels to target, e.g. VP or Director; one per line'),
    ],
  },
  {
    key: 'use_cases',
    title: 'Use cases',
    help: 'Scenarios where customers use the offering.',
    fields: [
      {
        path: '.',
        label: 'Use cases',
        kind: 'object-list',
        help: 'Concrete scenarios where customers adopt this offering.',
        itemFields: [
          text('name', 'Name', 'Short label for the use case'),
          text('trigger', 'Trigger', 'Event or situation that starts the need'),
          text('outcome', 'Outcome', 'Result the customer expects after adoption'),
        ],
      },
    ],
  },
  {
    key: 'customer_triggers',
    title: 'Customer triggers',
    help: 'Events indicating current need.',
    fields: [stringList('.', 'Triggers', 'Events that indicate a prospect may need this now; one per line')],
  },
  {
    key: 'pricing',
    title: 'Pricing',
    help: 'Model, price band, range, and minimum deal size.',
    fields: [
      text('model', 'Pricing model', 'How you charge, e.g. subscription, usage, or project', true),
      text('price_band', 'Price band', 'Relative price position, e.g. mid-market or enterprise premium'),
      text('typical_range', 'Typical price range', 'Usual price band for a standard deal'),
      text('min_deal_size', 'Minimum deal size', 'Smallest contract you will accept for this offering', true),
      text('sales_cycle', 'Sales cycle length', 'Typical time from first meeting to signed contract'),
      text('engagement_model', 'Engagement model', 'How delivery starts, e.g. pilot, POC, or full rollout'),
    ],
  },
  {
    key: 'competitors',
    title: 'Competitors',
    help: 'Who prospects use instead.',
    fields: [
      {
        path: '.',
        label: 'Competitors',
        kind: 'object-list',
        help: 'Alternatives prospects compare you against.',
        itemFields: [
          text('name', 'Name', 'Competitor company name'),
          text('website', 'Website', 'Competitor website URL'),
          {
            path: 'type',
            label: 'Type',
            kind: 'select',
            help: 'Direct rivals solve the same problem; indirect alternatives address it differently.',
            options: ['direct', 'indirect'],
          },
        ],
      },
    ],
  },
  {
    key: 'differentiators',
    title: 'Differentiators',
    help: 'Why customers choose you.',
    fields: [stringList('.', 'Differentiators', 'Reasons customers pick you over competitors; one per line')],
  },
  {
    key: 'implementation',
    title: 'Implementation',
    help: 'Setup effort and technical requirements.',
    fields: [
      text('setup_effort', 'Setup effort', 'Relative effort to go live, e.g. low, medium, or high'),
      text('onboarding_duration', 'Onboarding duration', 'Typical time until the customer is live'),
      stringList('technical_requirements', 'Technical requirements', 'Prerequisites on the customer side; one per line'),
      stringList('customer_resources', 'Customer resources required', 'People or systems the customer must provide; one per line'),
    ],
  },
  {
    key: 'integrations',
    title: 'Integrations',
    help: 'Software and ecosystems the offering works with.',
    fields: [
      stringList('must_have', 'Must-have integrations', 'Integrations required for a viable deal; one per line'),
      stringList('nice_to_have', 'Nice-to-have integrations', 'Integrations that improve fit but are not required; one per line'),
      stringList('ecosystems', 'Ecosystems', 'Marketplaces or partner ecosystems you support; one per line'),
    ],
  },
  {
    key: 'customer_success_stories',
    title: 'Customer success stories',
    help: 'At least five reference companies.',
    fields: [
      {
        path: '.',
        label: 'Success stories',
        kind: 'object-list',
        help: 'Reference customers agents can mention — add at least five.',
        itemFields: [
          text('name', 'Company name', 'Reference customer name'),
          text('website', 'Website', 'Reference customer website URL'),
          text('industry', 'Industry', 'Customer industry or segment'),
          area('why_they_bought', 'Why they bought', 'Trigger or pain that led to purchase'),
          area('outcome', 'Outcome', 'Result achieved after adoption'),
        ],
      },
    ],
  },
  {
    key: 'compliance_restrictions',
    title: 'Compliance / restrictions',
    help: 'Regions, certifications, legal, and technical limits.',
    fields: [
      stringList('regions_blocked', 'Regions blocked', 'Regions where you cannot sell or deploy; one per line'),
      stringList('certifications', 'Certifications', 'Certifications this offering satisfies; one per line'),
      area('legal_notes', 'Legal notes', 'Contract, privacy, or regulatory constraints'),
      stringList('technical_limits', 'Technical limits', 'Hard technical restrictions prospects should know; one per line'),
    ],
  },
  {
    key: 'keywords',
    title: 'Keywords',
    help: 'Terms prospects use when searching.',
    fields: [stringList('.', 'Keywords', 'Search terms prospects use for this problem or category; one per line')],
  },
  {
    key: 'signals',
    title: 'Signals',
    help: 'Public indicators of active need.',
    fields: [stringList('.', 'Signals', 'Public indicators that a company may need this offering; one per line')],
  },
  {
    key: 'exclusion_rules',
    title: 'Exclusion rules',
    help: 'Companies that are not a good fit.',
    fields: [
      stringList('rules', 'Exclusion rules', 'Hard rules that disqualify a company for this offering; one per line'),
      area('free_text', 'Other exclusion rules', 'Additional fit rules not captured above'),
    ],
  },
]

export const strategyFormSections: FormSectionDefinition[] = [
  {
    key: 'overview',
    title: 'Sales strategy overview',
    help: 'Name, description, and target narrative.',
    fields: [
      file('thumbnail_url', 'Thumbnail / Logo', 'Upload an image for the sales strategy'),
      text('name', 'Sales strategy name', 'Short label for this prospecting run', true),
      area('description', 'Description', 'What this strategy is trying to achieve and for which offering'),
      area('target_companies_narrative', 'Target companies in your own words', 'Describe ideal companies in plain language — agents use this to guide search', true),
    ],
  },
  {
    key: 'run_targets',
    title: 'Run targets',
    help: 'Operational quotas for this sales strategy.',
    fields: [
      num('target_companies', 'Target company count', 'How many companies to register for this strategy'),
      num('contacts_per_company_default', 'Default contacts per company', 'How many prospects to find per registered company'),
    ],
  },
  {
    key: 'target_decision_makers',
    title: 'Target decision makers',
    help: 'Roles to contact first.',
    fields: [
      stringList('primary_titles', 'Primary titles', 'First-choice job titles to contact; one per line'),
      stringList('secondary_titles', 'Secondary titles', 'Backup titles if primary contacts are unavailable; one per line'),
      {
        path: 'seniority_levels',
        label: 'Seniority levels',
        kind: 'multi-select',
        help: 'Target seniority tiers to focus on.',
        options: ['C-Suite', 'VP', 'Director', 'Head Of', 'Manager'],
      },
      {
        path: 'department_functions',
        label: 'Department functions',
        kind: 'multi-select',
        help: 'Department functions to target.',
        options: ['Engineering', 'Sales', 'Product', 'Marketing', 'IT', 'Finance', 'Operations'],
      },
      stringList('seniority_order', 'Seniority order', 'Preferred seniority sequence, e.g. VP then Director; one per line'),
      stringList('contact_buying_signals', 'Contact buying signals', 'Per-contact signals that indicate readiness; one per line'),
    ],
  },
  {
    key: 'target_company_profile',
    title: 'Target company profile',
    help: 'What kinds of companies to approach now.',
    fields: [
      stringList('company_types', 'Company types', 'Firm types to pursue, e.g. SaaS or manufacturer; one per line'),
      stringList('characteristics', 'Characteristics', 'Traits that make a company a strong fit; one per line'),
      {
        path: 'similar_companies',
        label: 'Similar companies',
        kind: 'object-list',
        help: 'Example companies that represent your ideal targets.',
        itemFields: [
          text('name', 'Name', 'Example company name'),
          text('website_url', 'Website URL', 'Example company website'),
        ],
      },
      stringList('keywords', 'Keywords', 'Terms to find lookalike companies; one per line'),
      stringList('problems_they_should_have', 'Problems they should have', 'Pains ideal targets should be feeling now; one per line'),
    ],
  },
  {
    key: 'priority_industries',
    title: 'Priority industries',
    help: 'Industries to focus on this run.',
    fields: [
      stringList('primary', 'Primary industries', 'Industries to prioritize in this run; one per line'),
      stringList('secondary', 'Secondary industries', 'Industries to include when quota allows; one per line'),
      stringList('deprioritized', 'Deprioritized industries', 'Industries to pursue only if no better matches; one per line'),
    ],
  },
  {
    key: 'priority_geographies',
    title: 'Priority geographies',
    help: 'Countries, regions, cities.',
    fields: [
      stringList('countries', 'Countries', 'Countries to target; one per line'),
      stringList('regions', 'Regions', 'Macro regions to include; one per line'),
      stringList('cities', 'Cities', 'Specific cities to prioritize; one per line'),
      { path: 'remote_only', label: 'Remote-only companies', kind: 'boolean', help: 'Limit targeting to fully remote or distributed companies only.' },
      stringList('exclude_countries', 'Exclude countries', 'Countries to skip; one per line'),
    ],
  },
  {
    key: 'company_size',
    title: 'Company size',
    help: 'Employee and revenue ranges.',
    fields: [
      num('employees_min', 'Employees min', 'Minimum employee count for target companies'),
      num('employees_max', 'Employees max', 'Maximum employee count for target companies'),
      num('revenue_min', 'Revenue min', 'Minimum annual revenue for target companies'),
      num('revenue_max', 'Revenue max', 'Maximum annual revenue for target companies'),
      stringList('segments', 'Segment tags', 'Labels for size or stage bands, e.g. mid-market; one per line'),
    ],
  },
  {
    key: 'buying_signals',
    title: 'Buying signals',
    help: 'Events indicating readiness now.',
    fields: [
      {
        path: 'selected',
        label: 'Selected signals',
        kind: 'multi-select',
        help: 'Select all that apply.',
        options: [
          'Hiring engineers / AI engineers / specific roles',
          'Recently funded / acquisition / IPO',
          'New office / international expansion',
          'New product launch / digital transformation / cloud migration',
          'Automation or AI initiative signals',
          'Growing engineering team / building AI products',
        ],
      },
      stringList('custom', 'Custom signals', 'Additional buying signals not listed above; one per line'),
    ],
  },
  {
    key: 'prospecting_strategy',
    title: 'Prospecting strategy',
    help: 'How Company Finder should discover companies.',
    fields: [
      {
        path: 'sources',
        label: 'Sources',
        kind: 'multi-select',
        help: 'Where Company Finder should look for matching companies.',
        options: [
          'LinkedIn',
          'Crunchbase',
          'Product Hunt',
          'YC',
          'App stores',
          'VC portfolios',
          'Careers pages',
          'GitHub',
          'News',
          'AngelList / Wellfound',
          'Google',
          'Apollo',
        ],
      },
      stringList('excluded_domain_types', 'Excluded domain types', 'Types of sites to skip during discovery, e.g. Job boards, Blog aggregators; one per line'),
    ],
  },
  {
    key: 'competitor_targeting',
    title: 'Competitor targeting',
    help: 'Incumbents that make good targets.',
    fields: [
      stringList('incumbents_to_target', 'Incumbents to target', 'Competitor products customers may want to replace; one per line'),
      stringList('switch_triggers', 'Switch triggers', 'Events that push buyers to switch away from incumbents; one per line'),
      stringList('avoid_unless_scaling', 'Avoid unless scaling', 'Incumbents to skip unless the company is growing fast; one per line'),
    ],
  },
  {
    key: 'qualification_criteria',
    title: 'Qualification criteria',
    help: 'What makes a company worth pursuing.',
    fields: [
      stringList('must_have', 'Must-have attributes', 'Traits a company must have to pursue; one per line'),
      stringList('nice_to_have', 'Nice-to-have attributes', 'Traits that improve priority but are not required; one per line'),
      num('min_confidence_hint', 'Minimum confidence hint', 'Lowest agent confidence score to keep a company on the list'),
    ],
  },
  {
    key: 'prioritization_rules',
    title: 'Prioritization rules',
    help: 'Who to contact or validate first.',
    fields: [stringList('rules', 'Rules', 'How to rank companies or contacts when quota is tight; one per line')],
  },
  {
    key: 'exclusion_rules',
    title: 'Exclusion rules',
    help: 'Hard rules and exclusions for skipping companies or prospects.',
    fields: [
      stringList('rules', 'Exclusion rules', 'Conditions that disqualify a company from outreach; one per line'),
      stringList('companies', 'Companies', 'Named companies to never contact; one per line'),
      stringList('domains', 'Domains', 'Email or web domains to block; one per line'),
      stringList('industries', 'Industries', 'Industries to exclude from this run; one per line'),
      stringList('regions', 'Regions', 'Regions to exclude from this run; one per line'),
    ],
  },
  {
    key: 'experiments',
    title: 'Experiments',
    help: 'What the team is actively testing.',
    fields: [
      {
        path: '.',
        label: 'Experiments',
        kind: 'object-list',
        help: 'Active tests you want agents and operators to run.',
        itemFields: [
          text('hypothesis', 'Hypothesis', 'What you are trying to learn'),
          text('variant', 'Variant', 'What is different in this test'),
          text('success_criteria', 'Success criteria', 'How you will judge success'),
          area('notes', 'Notes', 'Setup details or constraints for this experiment'),
        ],
      },
    ],
  },
  {
    key: 'success_metrics',
    title: 'Success metrics',
    help: 'Operator-defined run targets.',
    fields: [stringList('targets', 'Targets', 'Measurable goals for this run, e.g. meetings booked; one per line')],
  },
]
