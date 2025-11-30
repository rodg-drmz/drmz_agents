# drmz_crewai Folder Cleanup

## Status: ✅ Safe to Remove/Archive

The `drmz_crewai/` folder is **legacy code** that has been replaced by the `src/drmz/` structure.

## What's in drmz_crewai/

```
drmz_crewai/
├── agents/          # ❌ Old agent YAML files (replaced by src/drmz/academy_agents/)
├── crews/           # ❌ Old crew definitions (replaced by src/drmz/crews/)
├── flows/           # ❌ Old flow implementations (replaced by src/drmz/flows/)
├── tasks/           # ❌ Old task configs (replaced by src/drmz/config/tasks.yaml)
└── outputs/         # ❌ Old outputs (replaced by output/)
```

## Current System (src/drmz/)

The active codebase uses:
- ✅ `src/drmz/flows/` - All flow implementations
- ✅ `src/drmz/config/` - Unified YAML configs (agents.yaml, tasks.yaml)
- ✅ `src/drmz/crews/` - Crew definitions
- ✅ `src/drmz/academy_agents/` - Agent YAML files

## References to drmz_crewai

### In pyproject.toml (CLI Commands)
```toml
guide_flow = "drmz_crewai.flows.guide_creator_flow:kickoff"
morpheus_chat = "drmz_crewai.flows.morpheus_chat_flow:kickoff"
morpheus_api = "drmz_crewai.flows.morpheus_chat_flow:chat_endpoint"
```

**Status**: These CLI commands are **not used by the dApp**. They're only for standalone CLI usage.

### Not Used By
- ❌ dApp (`drmz-dapp/`) - Uses `/api/agents/chat/[slug]` → `morpheus-agent-gw` or `src/drmz/`
- ❌ Current flows - All use `src/drmz/flows/`
- ❌ Current agents - All use `src/drmz/config/agents.yaml` and `src/drmz/academy_agents/`

## Action Plan

### Option 1: Archive (Recommended)
```bash
cd /Users/rodg/Documents/Projects/drmz_agents
tar -czf drmz_crewai_archive_$(date +%Y%m%d).tar.gz drmz_crewai/
rm -rf drmz_crewai/
```

### Option 2: Remove Completely
```bash
cd /Users/rodg/Documents/Projects/drmz_agents
rm -rf drmz_crewai/
```

### Update pyproject.toml (After Removal)
Remove or comment out these lines:
```toml
# Legacy crew scripts (not used by dApp)
# guide_flow = "drmz_crewai.flows.guide_creator_flow:kickoff"
# morpheus_chat = "drmz_crewai.flows.morpheus_chat_flow:kickoff"
# morpheus_api = "drmz_crewai.flows.morpheus_chat_flow:chat_endpoint"
```

And update:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]  # Remove "drmz_crewai"
```

## Verification

After removal, verify:
- ✅ dApp still works (uses `src/drmz/` system)
- ✅ Flows still work (all in `src/drmz/flows/`)
- ✅ Agents still work (all in `src/drmz/config/` and `src/drmz/academy_agents/`)

## Summary

**drmz_crewai/** is safe to remove because:
1. ✅ All functionality moved to `src/drmz/`
2. ✅ dApp doesn't use it
3. ✅ Current flows don't import from it
4. ✅ Only referenced in unused CLI commands

