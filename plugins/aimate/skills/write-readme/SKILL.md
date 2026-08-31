---
name: Write readme
description: Use this skill whenever the user asks to create, write, generate, improve, or standardize a README for a codebase or repository, or mentions that a project is missing documentation. Applies to any language or stack (dotnet, Node, Python, etc). Always use this skill instead of freestyling a README structure - it enforces a consistent, company-wide layout so every project's README looks and reads the same way.
---

# Write README

Generates a clear, consistent, high-level README for a codebase. One predictable structure across all company projects — not an exhaustive technical dump. A README should orient a new developer in five minutes, not replace the code.

## Rules

- Skip a section entirely if the information is not present in the codebase — never guess or invent.
- Omit sections that don't apply; never leave placeholders.
- Prefer tables and short bullets over prose.
- Never generate a full file tree — stop at project/module level.
- Never add a license/ownership section unless explicitly asked.
- Never write actual secret values.
- Keep language plain — no marketing tone, no filler.
- Always use the same section order and emoji headers below.

## Process

1. **Check for an existing README.md** — if one exists and is clearly well-maintained (good structure, real content, obvious effort), ask the user before proceeding: *"There is already a detailed README. Do you want to replace it, or only bring it in line with the standard style?"*
2. **Explore the repository structure** (solutions/projects, folders, config files, test folders, CI config) to understand what the project is and does.
3. **Use any existing README as a secondary source only** — extract useful facts not derivable from the codebase (port numbers, external dependencies, known quirks, manual steps) and place them under the appropriate section. Do not copy structure or phrasing.
4. **Write the README** to `README.md` at the repo root, following the section order below.

## Sections (in this order)

### 1. 📌 Title + one-line description
Project name with a fitting emoji, followed by exactly one sentence explaining what the project does and why it exists.

### 2. 🛠️ Dev setup
A short "Getting Started" pointer. If a `docs/Setup.md` (or equivalent) exists, link to it. If not, create it with a minimal template: prerequisites, clone, restore/build command, run command. Secrets and config go in section 7, not here.

### 3. 📋 Table of Contents
Only include if the README has more than ~5 headers.

### 4. 🗺️ Overview
A high-level explanation of what the system does and how the pieces fit together, ideally with a Mermaid diagram (`graph LR` or `sequenceDiagram`), capped at 4–6 steps. Describe the concept, not the code — no class names, method names, or file paths.

### 5. 📁 Project structure
List each project/module with one line describing its responsibility. Never go deeper than project/module level.

### 6. 🗄️ Database
Only include if the project has a database:
- Database type (SQL Server, Postgres, SQLite, etc.)
- How migrations are managed and the command to run them
- Optionally, a short table of top-level tables with a one-line description each (no columns, no schema details)

### 7. 🔐 Configuration & Secrets
Where secrets/config live (vault, secret manager, appsettings, env vars) and who to contact for access.

### 8. 🧪 Testing
Test framework, command to run tests, and optionally which layers are covered (unit/integration).

### 9. 🚀 CI/CD & Cloud
Pipeline tool, what each stage does, deployment target, and cloud infrastructure setup — only if this information is available from config files (e.g. `.gitlab-ci.yml`, Kubernetes manifests, Terraform). Never invent cloud details.
