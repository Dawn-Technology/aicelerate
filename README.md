# aicelerate — AI Acceleration Repository

An agent plugin marketplace by Dawn Technology, containing the `aimate` plugin with reusable skills for security auditing, GitLab workflow automation, and development planning.

## Install

### Visual Studio Code

#### Via the marketplace (recommended)

1. Open your VS Code `settings.json` and add the marketplace:

   ```json
   "chat.plugins.marketplaces": [
       "Dawn-Technology/aicelerate"
   ]
   ```

2. Open the Extensions view (`⇧⌘X`) and search for `@agentPlugins`.

3. Find `aimate` and select **Install**.

#### Direct install from source

Run **Chat: Install Plugin From Source** from the Command Palette and enter:

```
https://github.com/Dawn-Technology/aicelerate
```

#### Update

Run **Extensions: Check for Extension Updates** from the Command Palette.

### GitHub Copilot CLI

#### Via the marketplace (recommended)

Register the marketplace once, then install by name:

```bash
copilot plugin marketplace add Dawn-Technology/aicelerate
copilot plugin install aimate@aicelerate
```

#### Direct install

```bash
copilot plugin install Dawn-Technology/aicelerate:plugins/aimate
```

#### Update

```bash
copilot plugin update aimate
```

## Requirements

### Visual Studio Code

- GitHub Dawn Technology organization account with Copilot seat enabled

- Visual Studio Code with the [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extension installed
  - Agent plugin support enabled (`chat.plugins.enabled: true` in settings)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli) installed and authenticated

## Recommended external skills

The following skills are not part of this repository but are recommended for use alongside `aimate`.

### Grill Me ([mattpocock/skills — grill-me](https://github.com/mattpocock/skills/blob/main/grill-me))

Interviews you relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree one question at a time. Use when you want to stress-test a plan or get grilled on a design.

```bash
npx skills add https://github.com/mattpocock/skills --skill grill-me
```

### ADR Writing ([vercel/ai — adr-skill](https://skills.sh/vercel/ai/adr-skill))

Helps agents write Architectural Decision Records (ADRs) as executable specifications — structured enough for a coding agent to implement without follow-up questions.

```bash
npx skills add https://github.com/vercel/ai --skill adr-skill
```

## Plugin

See the [aimate plugin README](plugins/aimate/README.md) for available skills and usage details.
