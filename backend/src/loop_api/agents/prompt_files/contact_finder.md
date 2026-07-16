# Prospect Discovery Prompt

## Objective

Your objective is to identify the **best people within the target company** who are most likely to influence, evaluate, recommend, approve, or purchase the offered solution.

Do **not** return every employee.

Return only the highest-value prospects based on the provided sales strategy.

---

# Target Company

Company Name:
{{company_name}}

Website:
{{company_website}}

Company Summary:
{{company_summary}}

Industry:
{{industry}}

Employee Count:
{{employee_count}}

---

# Sales Objective

{{sales_objective}}

Example

- Sell AI customer support software
- Sell custom software development
- Sell cloud migration services

---

# Solution Category

{{solution_category}}

Examples

- CRM
- Cybersecurity
- HR Software
- AI Platform
- ERP
- Software Development Services
- Cloud Services

---

# Buying Committee

Identify prospects that match the following buying roles.

{{target_roles}}

Examples

- Economic Buyer
- Decision Maker
- Budget Owner
- Technical Evaluator
- Business Owner
- End User Champion
- Procurement
- Executive Sponsor

---

# Preferred Job Titles

Prioritize people with titles similar to:

{{preferred_job_titles}}

Examples

- CTO
- VP Engineering
- Head of IT
- CIO
- Director of Customer Support
- COO
- Head of Operations

---

# Department Priority

Search these departments first.

{{target_departments}}

Examples

- Engineering
- IT
- Customer Support
- Operations
- HR
- Finance
- Marketing
- Sales

---

# Qualification Criteria

Prioritize prospects that satisfy as many of these conditions as possible.

{{prospect_qualification_criteria}}

Examples

- Owns the business problem
- Has budget authority
- Leads the relevant department
- Responsible for technology decisions
- Responsible for operations
- Can influence purchasing
- Works closely with executive leadership

---

# Exclusion Rules

Do not include prospects matching these conditions.

{{prospect_exclusion_rules}}

Examples

- Recruiters
- Interns
- Individual Contributors without influence
- Students
- Contractors
- Advisors
- Former employees

---

# Prioritization Rules

Rank prospects using the following order.

{{prioritization_rules}}

Example

1. Decision-making authority
2. Ownership of the business problem
3. Budget influence
4. Technical influence
5. Seniority
6. Relevance of department
7. Public activity indicating responsibility

---

# Search Constraints

{{search_constraints}}

Examples

- Current employees only
- Publicly verifiable information only
- Prefer LinkedIn profiles
- Prefer employees active within the last year

---

# Expected Output

For each prospect provide:

- Full Name
- Current Job Title
- Department
- Seniority
- LinkedIn Profile (if available)
- Public Email (only if publicly available)
- Public Phone (only if publicly available)
- Location
- Why they are relevant
- Role in Buying Committee
- Estimated Decision Influence
- Confidence Score (0–100)

---

# Decision Guidelines

While identifying prospects:

1. Focus on who is most likely to own the problem being solved.
2. Prefer responsibility over seniority.
3. A department head may be a better prospect than a C-level executive if they own the initiative.
4. Include multiple buying committee members only when each serves a different role.
5. Avoid returning duplicate or overlapping roles.
6. If the exact title is unavailable, identify the closest equivalent.
7. Base conclusions only on publicly available evidence.
8. State uncertainty instead of making assumptions.

---

# Important

Your objective is **not** to find every employee.

Your objective is to identify the **smallest set of people who are most likely to drive or influence the purchasing decision** for the provided sales objective.

Return quality over quantity.
