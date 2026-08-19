# Project Collaboration Rules

## Task records

- For every project-related user interaction, update `tasks/communicating.md` before the final response with the timestamp (Asia/Shanghai), interaction number, agent identity, user intent, actions or checks, files written by that agent, decisions, and unresolved items.
- Attribute only work that can be verified in the current interaction. If an older entry lacks a reliable agent identity or exact timestamp, mark it as unknown instead of inferring one.
- When an interaction changes project state, also update the relevant files:
  - unresolved decisions or missing information → `tasks/question.md`
  - complete task pool and status → `tasks/todo.md`
  - immediately actionable priorities → `tasks/next-todo.md`
  - recommendations, uncertainties, omissions, and risks → `tasks/advice.md`
- Keep facts, decisions, and recommendations distinct. Do not invent requirements, architecture, visual details, execution results, or acceptance evidence that are absent from the source documents or tool output.
- When PRD, technical specification, or visual-design sources are added or changed, record their path and version/date before deriving or revising tasks.
