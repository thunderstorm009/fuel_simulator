# Master bootstrap: use ONCE, before Sprint 1 (planning and discovery only)

Paste COMMON-HEADER.md first. Do not write application code in this step.

Read AGENTS.md, PROJECT_PLAN.md, docs/architecture.md, docs/simulator-contract.md, docs/intelligence.md, docs/resilience.md, and the official brief and simulator guide in reference/ (extract their text if they are PDFs).

Tasks:
1. Assess the repository: is it empty apart from the kit, or does it already contain application code? List what exists. Preserve any working code.
2. Compare the official sources with docs/simulator-contract.md. List every mismatch and every item marked VERIFY. Do not guess.
3. Confirm that the P0 workflow fits 28 hours with the architecture in PROJECT_PLAN.md. Say what you would simplify and why (for example fewer containers), and record proposals in docs/decisions.md as PROPOSED.
4. For each of the seven sprints give: the work packages, the order, the riskiest item and a time box. Make sure sprint 2 and later extend earlier work and never recreate it.
5. List questions that need my decision.

Output: repository assessment, contract mismatches and unknowns, architecture confirmation or changes, seven-sprint plan, P0/P1/P2 list, questions.
Then update docs/PROGRESS.md (state: Sprint 0 complete, plan approved or not) and stop. Wait for approval.
