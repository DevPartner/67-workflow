# Task Implementation Instructions

Source: https://github.com/github/awesome-copilot/blob/main/instructions/task-implementation.instructions.md

These instructions apply whenever implementing tasks from `.copilot-tracking/plans/` and `.copilot-tracking/details/`.

## Core Implementation Process

### 1. Plan Analysis and Preparation

Before starting any implementation:

- Read the complete plan file including scope, objectives, all phases, and every checklist item
- Read the corresponding changes file in `.copilot-tracking/changes/` completely; if context is missing, re-read the entire file
- Identify all referenced files mentioned in the plan and examine them for context
- Understand current project structure and conventions

### 2. Systematic Implementation Process

Implement each task in the plan in order:

1. **Process tasks sequentially** — follow the plan sequence exactly, one task at a time
2. **Before implementing any task**:
   - Ensure the implementation is associated with a specific task from the plan
   - Read the entire details section for that task from `.copilot-tracking/details/**`
   - Fully understand all implementation details before writing any code
3. **Implement the task completely**:
   - Follow existing code patterns and conventions from the workspace
   - Create working functionality that meets all task requirements
   - Include proper error handling and follow best practices
4. **After completing each task**:
   - Update plan file: change `[ ]` to `[x]` for the completed task
   - Append to the changes file (Added / Modified / Removed sections) with relative file path and one-sentence summary
   - If changes diverge from the plan, call this out explicitly in the changes file with the specific reason
   - If ALL tasks in a phase are complete, mark the phase header `[x]`

### 3. Implementation Quality Standards

Every implementation must:

- Follow existing workspace patterns and conventions
- Implement complete, working functionality that meets all task requirements
- Include appropriate error handling and validation
- Use consistent naming conventions and code structure from the workspace
- Ensure compatibility with existing systems and dependencies

### 4. Continuous Progress and Validation

After implementing each task:

1. Validate changes against the task requirements from the details file
2. Fix any problems before moving to the next task
3. Update the plan file to mark completed tasks `[x]`
4. Update the changes file with Added / Modified / Removed entries
5. Continue to the next unchecked task

Continue until all tasks are marked `[x]`, all specified files exist with working code, and all success criteria are verified.

### 5. Completion and Documentation

Implementation is complete when:

- All plan tasks are marked `[x]`
- All specified files exist with working code
- All success criteria from the plan are verified
- No implementation errors remain

**Final step**: Add a Release Summary section to the changes file only after ALL phases are marked complete.

### 6. Problem Resolution

When encountering implementation issues:

- Document the specific problem clearly
- Try alternative approaches
- Use workspace patterns as fallback when external references fail
- Continue with available information rather than stopping
- Note unresolved issues in the plan file for future reference

## Implementation Workflow

```
1. Read plan file and all checklists completely
2. Read changes file completely (re-read if missing context)
3. For each unchecked task:
   a. Read entire details section from .copilot-tracking/details/**
   b. Fully understand all implementation requirements
   c. Implement with working code following workspace patterns
   d. Validate implementation meets task requirements
   e. Mark task complete [x] in plan file
   f. Append to changes file (Added / Modified / Removed)
   g. Call out any divergences from plan with specific reasons
4. Repeat until all tasks complete
5. Only after ALL phases complete [x]: add Release Summary to changes file
```

## Success Criteria

- All plan tasks marked `[x]`
- All specified files contain working code
- Code follows workspace patterns and conventions
- Changes file updated after every task with Added / Modified / Removed entries
- Changes file includes final Release Summary after all phases complete

## Changes File Template

Create in `.copilot-tracking/changes/` with filename `YYYYMMDD-task-description-changes.md`.
Update after **every** task completion by appending to the relevant section.

```markdown
<!-- markdownlint-disable-file -->
# Release Changes: {{task name}}

**Related Plan**: {{plan-file-name}}
**Implementation Date**: {{YYYY-MM-DD}}

## Summary

{{Brief description of the overall changes made for this release}}

## Changes

### Added

- {{relative-file-path}} — {{one sentence summary of what was implemented}}

### Modified

- {{relative-file-path}} — {{one sentence summary of what was changed}}

### Removed

- {{relative-file-path}} — {{one sentence summary of what was removed}}

## Release Summary

**Total Files Affected**: {{number}}

### Files Created ({{count}})

- {{file-path}} — {{purpose}}

### Files Modified ({{count}})

- {{file-path}} — {{changes-made}}

### Files Removed ({{count}})

- {{file-path}} — {{reason}}

### Dependencies & Infrastructure

- **New dependencies**: {{list}}
- **Updated dependencies**: {{list}}
- **Configuration updates**: {{list}}

### Deployment Notes

{{Any specific deployment considerations or steps}}
```

## Tracking Directory Structure

```text
.copilot-tracking/
├── research/    ← YYYYMMDD-task-description-research.md  (task-researcher skill)
├── plans/       ← YYYYMMDD-task-description-plan.md      (task-planner skill)
├── details/     ← YYYYMMDD-task-description-details.md   (task-planner skill)
├── prompts/     ← implement-task-description.prompt.md   (task-planner skill)
└── changes/     ← YYYYMMDD-task-description-changes.md   (this file — written during implementation)
```

## Available Skills

- `/task-researcher` — research a topic, produce a research file in `.copilot-tracking/research/`
- `/task-planner` — validate research, produce plan + details + prompt files
- `/sb-logging` - Verbose Logging Conventions

---

# MCP Research Priority

For any research task, **always try MCP sources first** before falling back to WebSearch or WebFetch.

| Goal | MCP server |
|------|-----------|
| Microsoft-specific documentation | `microsoftdocs/mcp` |
| Deep repository or wiki exploration | `cognitionai/deepwiki` |
| Library, framework, or npm package docs | `upstash/context7` |

## Context7 Lookup Steps

When researching any library, framework, or package:

1. Call `mcp_context7_resolve-library-id({ libraryName: "..." })` to find the canonical ID
2. Select the result with the **highest score**
3. Call `mcp_context7_get-library-docs({ context7CompatibleLibraryID: "...", topic: "..." })`
4. Set `tokens`:
   - `5000` for standard feature lookups
   - `7000–10000` for complex integrations or deep-dive topics
5. **Fallback to WebSearch/WebFetch only if Context7 returns no usable results**
