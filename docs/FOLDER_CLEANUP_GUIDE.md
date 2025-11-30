# Folder Cleanup Guide

## ✅ Keep These Folders

### Core Structure
- `src/drmz/` - Main agent code (flows, crews, config, tools, utils)
- `data/knowledge/` - Knowledge base files (frameworks, outcomes, etc.)
- `output/` - Generated outputs (reviews, analyses) - these are downloadable
- `.temp/uploads/` - Temporary file storage (auto-cleaned after 24h)

### Configuration
- `src/drmz/config/` - Agent and task YAML configs
- `pyproject.toml` - Python project config
- `requirements.txt` - Python dependencies

## ❌ Remove/Archive These

### 1. `drmz_crewai/` (OLD - Not Used by DApp) ⚠️ **SAFE TO REMOVE**
**Status**: Legacy code, completely replaced by `src/drmz/`
**Action**: Archive or remove - see `docs/DRMZ_CREWAI_CLEANUP.md` for details
**Note**: Only referenced in `pyproject.toml` for unused CLI commands
**Impact**: None - dApp uses `src/drmz/` system exclusively

### 2. `data/syllabus/` - Old Uploaded Files
**Status**: Contains old uploaded PDFs and batch folders
**Action**: Clean up old files, keep structure for batch processing
**Keep**: Empty folder structure for batch ZIP processing
**Remove**: 
- Individual PDF files (e.g., `Honors_English_101_Syllabus_*.pdf`)
- Old batch folders (keep only recent ones if needed)

### 3. `data/assignments/` - Should Be Empty
**Status**: Should not store uploaded files
**Action**: Keep folder but ensure it stays empty (files use temp system)

### 4. `knowledge/` (Root Level) - Duplicate
**Status**: Old knowledge folder, duplicate of `data/knowledge/`
**Action**: Archive or remove - use `data/knowledge/` instead

### 5. `data/execution/` - CrewAI Execution Logs
**Status**: SQLite databases from CrewAI execution tracking
**Action**: Can be cleaned periodically (these are execution logs)

### 6. Old Batch Folders
**Location**: `data/syllabus/batch_*`
**Action**: Remove old batch folders after processing is complete

## 📁 Recommended Structure

```
drmz_agents/
├── src/drmz/              # ✅ Main agent code
│   ├── flows/             # ✅ All flow scripts
│   ├── config/            # ✅ YAML configs
│   ├── crews/             # ✅ Crew definitions
│   ├── tools/             # ✅ Tools and utilities
│   └── utils/             # ✅ Helper functions
├── data/
│   ├── knowledge/         # ✅ Knowledge base (frameworks, outcomes)
│   ├── syllabus/          # ⚠️  Keep for batch processing, clean old files
│   └── assignments/       # ⚠️  Keep empty (temp files only)
├── output/                # ✅ Generated outputs (downloadable)
│   ├── assignments/       # ✅ Assignment analyses
│   └── curriculum/        # ✅ Syllabus reviews
├── .temp/uploads/         # ✅ Temp files (auto-cleaned)
└── docs/                  # ✅ Documentation
```

## 🧹 Cleanup Commands

### Remove old uploaded files from data/syllabus/
```bash
cd /Users/rodg/Documents/Projects/drmz_agents
# Remove individual PDF files (keep batch folders for now)
find data/syllabus -maxdepth 1 -name "*.pdf" -type f -delete

# Remove old batch folders (older than 30 days)
find data/syllabus -type d -name "batch_*" -mtime +30 -exec rm -rf {} +
```

### Archive drmz_crewai (if not needed)
```bash
# Create archive
tar -czf drmz_crewai_archive.tar.gz drmz_crewai/

# Remove original (after verifying archive)
rm -rf drmz_crewai/
```

### Clean execution logs
```bash
# Remove old execution logs (older than 7 days)
find data/execution -type f -name "*.db" -mtime +7 -delete
```

## 📝 Notes

- **Temp Files**: All uploaded files now use `.temp/uploads/` and are auto-cleaned after 24 hours
- **Output Files**: Only analysis results are saved to `output/` - these are downloadable
- **Knowledge Base**: Use `data/knowledge/` for all framework and standards files
- **No Permanent Storage**: Uploaded files are never permanently stored - only outputs are saved

