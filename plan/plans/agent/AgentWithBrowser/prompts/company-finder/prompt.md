# Company Prospect Identification Prompt

## Objective

Your objective is to identify companies that are highly likely to become qualified prospects based on the provided sales strategy.

Do **not** search for people or decision makers.
Your output should only contain companies that closely match the target profile.

---

# Sales Objective

{{sales_objective}}

Example:
- Find companies that would benefit from our AI customer support platform.
- Find manufacturing companies likely to outsource software development.
- Find logistics companies preparing for digital transformation.

---

# Ideal Target Company Profile (ICP)

## Industries

{{target_industries}}

---

## Company Size

{{company_size}}

Examples:
- 50–500 employees
- 100M–1B annual revenue
- Enterprise only
- SMB only

---

## Geographic Scope

{{target_regions}}

---

## Business Characteristics

{{business_characteristics}}

Examples

- B2B SaaS
- Healthcare Providers
- FinTech
- Manufacturing
- VC-backed startups
- Public companies
- Fast-growing businesses

---

# Qualification Criteria

A company should satisfy as many of these criteria as possible.

{{qualification_criteria}}

Examples

- Uses Microsoft ecosystem
- Has internal sales team
- Offers subscription products
- Operates globally
- Has engineering organization
- Provides customer support
- Growing internationally

---

# Buying Signals

Prioritize companies showing these signals.

{{buying_signals}}

Examples

- Recent funding
- Rapid hiring
- International expansion
- Opening new offices
- Launching new products
- Hiring AI engineers
- Hiring sales teams
- Digital transformation initiatives
- Recent acquisitions

---

# Exclusion Rules

Never include companies matching these conditions.

{{exclusion_rules}}

Examples

- Less than 20 employees
- Government organizations
- Non-profits
- Existing customers
- Competitor companies
- Outside target geography

---

# Priority Rules

When multiple companies qualify, prioritize those that best satisfy the following:

{{priority_rules}}

Example

1. Buying signals
2. ICP match
3. Company growth
4. Technology maturity
5. Geographic preference

---

# Search Constraints

{{search_constraints}}

Examples

- Only active companies
- Only independent companies
- Exclude subsidiaries
- Exclude stealth startups
- Exclude companies with missing employee counts

---

# Expected Output

For every company return:

- Company Name
- Website
- Industry
- Headquarters
- Employee Range
- Estimated Revenue (if available)
- Short Description
- Why it matches the ICP
- Buying Signals Found
- Confidence Score (0–100)

---

# Instructions

1. Search broadly before narrowing results.
2. Evaluate companies against the ICP, not individual products.
3. Use multiple qualification factors instead of a single matching attribute.
4. Prioritize companies with strong buying signals.
5. Skip companies that violate any exclusion rule.
6. If information is uncertain, state the uncertainty instead of assuming.
7. Rank companies from strongest match to weakest.
8. Prefer quality over quantity.
9. Return only companies with a meaningful likelihood of becoming prospects.
10. Explain briefly why each company was selected.

---

# Important

Your goal is **not** to find every company.

Your goal is to identify the companies **most likely to become qualified sales opportunities** according to the provided sales strategy.
