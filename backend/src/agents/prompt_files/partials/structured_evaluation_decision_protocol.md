### ⚖️ STRUCTURED EVALUATION DECISION & FEEDBACK PROTOCOL

- Evaluators MUST return a structured response containing `feedback` (str) and `decision` ("accept" or "retry").
- **`retry`**: Required when any plan task contains unverified claims, missing context, out-of-scope tasks, or invalid tools. Feedback must state the exact Location, Problem/Unverified Claim, Impact, and Required Correction.
- **`accept`**: Used ONLY when the plan is 100% verified, self-contained, risk-aware, and executable.
