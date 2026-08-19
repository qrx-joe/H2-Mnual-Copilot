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

## Version control and code explanation

- The workspace is a local Git repository. After each completed step (a document update, a code change, or a verified fix), commit immediately with a message that states what the step did; do not batch unrelated changes into one commit. Pushing to a remote or touching external systems still requires separate user authorization.
- Whenever code is written or modified, explain it: in the response, state the purpose, approach, and scope of the change in the user's language; in the code, comment key logic and non-obvious constraints at a density matching the surrounding code.
