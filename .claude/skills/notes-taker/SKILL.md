---
name: notes-taker
description: Take and organize learning notes in readable markdown format. Use when user says "take notes on [topic]", "add notes about [topic]", "I'm learning [topic]", "/notes [topic]", or asks to document what they're learning. Creates topic-based markdown files with structured sections.
---

# Notes Taker

Take structured learning notes organized by topic into readable markdown files.

## Workflow

1. Identify the topic from user input
2. Determine notes file path: `notes/<topic>.md` (create `notes/` dir if needed)
3. If file exists, append new content under appropriate section
4. If new file, create with structured template

## File Structure

```
notes/
├── kubernetes.md
├── docker.md
├── python.md
└── ...
```

## Note Format

Use this structure for each topic file:

```markdown
# [Topic Name]

## Overview
Brief summary of what this topic covers.

## Key Concepts

### [Concept Name]
- Point 1
- Point 2

## Commands & Syntax

```bash
# Description of command
command --flag argument
```

## Examples

### [Example Name]
Description and code/demonstration.

## Tips & Best Practices
- Tip 1
- Tip 2

## Resources
- [Link text](url)
```

## Adding Notes

When user provides new information:

1. Read existing file if present
2. Identify which section the new content belongs to
3. Add under existing section header, or create new subsection
4. Keep notes concise - bullet points preferred
5. Include code blocks with language hints for syntax highlighting

## Example Interaction

User: "take notes on kubernetes - pods are the smallest deployable unit"

Action:
1. Check if `notes/kubernetes.md` exists
2. If not, create with template
3. Add under "Key Concepts":

```markdown
### Pods
- Smallest deployable unit in Kubernetes
- Contains one or more containers
```
