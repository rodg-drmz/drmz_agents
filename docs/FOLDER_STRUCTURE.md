# DRMZ Agents Folder Structure

## ✅ Current Structure (Streamlined)

```
drmz_agents/
├── src/drmz/                    # ✅ Main agent code
│   ├── flows/                   # ✅ All flow scripts
│   │   ├── syllabus/            # ✅ Syllabus review flows
│   │   └── assignment/         # ✅ Assignment analysis flows
│   ├── config/                  # ✅ YAML configs (agents, tasks)
│   ├── crews/                   # ✅ Crew definitions
│   ├── tools/                   # ✅ Tools and utilities
│   ├── utils/                   # ✅ Helper functions
│   └── knowledge_graph/         # ✅ Knowledge graph RAG tool
│
├── data/                        # ✅ Data storage
│   ├── knowledge/               # ✅ Knowledge base (frameworks, standards)
│   │   ├── inclusivity_frameworks/
│   │   ├── learning_outcomes/
│   │   └── pedagogical_frameworks/
│   ├── syllabus/                # ⚠️  Batch processing only (ZIP files)
│   └── assignments/             # ⚠️  Should stay empty (temp files only)
│
├── output/                      # ✅ Generated outputs (downloadable)
│   ├── assignments/             # ✅ Assignment analyses
│   │   ├── ai_review/
│   │   ├── ai_meter/
│   │   └── ai_redesign/
│   └── curriculum/              # ✅ Syllabus reviews
│       ├── policy_reviews/
│       ├── outcomes_checks/
│       └── inclusivity_evaluations/
│
├── .temp/uploads/               # ✅ Temp file storage (auto-cleaned after 24h)
│
└── docs/                        # ✅ Documentation
```

## 📋 File Flow

### Upload Process
1. **User uploads file** → Stored in `.temp/uploads/` with UUID
2. **API receives tempId** → Uses temp file directly (no copying)
3. **Python flow processes** → Reads from temp file
4. **Result saved** → Only to `output/` (downloadable)
5. **Temp file cleaned** → Auto-deleted after 24 hours

### No Permanent Storage
- ❌ Uploaded files are **never** saved permanently
- ✅ Only analysis **outputs** are saved (in `output/`)
- ✅ Users can download outputs via UI
- ✅ Temp files auto-clean after 24 hours

## 🗑️ Folders to Clean/Remove

### 1. `drmz_crewai/` (OLD)
- **Status**: Old structure, replaced by `src/drmz/`
- **Action**: Archive or remove (only used in old CLI commands)
- **Impact**: None on dApp functionality

### 2. `knowledge/` (Root Level)
- **Status**: Duplicate of `data/knowledge/`
- **Action**: Archive or remove
- **Impact**: None (use `data/knowledge/` instead)

### 3. `data/syllabus/` - Old Files
- **Status**: Contains old uploaded PDFs
- **Action**: Run cleanup script to remove individual PDFs
- **Keep**: Folder structure for batch ZIP processing

### 4. `data/execution/` - Old Logs
- **Status**: CrewAI execution tracking databases
- **Action**: Can be cleaned periodically (older than 7 days)

## 🧹 Cleanup Commands

### Quick Cleanup
```bash
cd /Users/rodg/Documents/Projects/drmz_agents
./scripts/cleanup_old_files.sh
```

### Manual Cleanup
```bash
# Remove old PDFs from data/syllabus
find data/syllabus -maxdepth 1 -name "*.pdf" -type f -delete

# Remove old batch folders (30+ days)
find data/syllabus -type d -name "batch_*" -mtime +30 -exec rm -rf {} +

# Clean execution logs (7+ days)
find data/execution -type f -name "*.db" -mtime +7 -delete

# Ensure assignments folder is empty
find data/assignments -type f -delete
```

## 📝 Notes

- **Temp System**: All uploads use `.temp/uploads/` - no permanent storage
- **Output Only**: Only analysis results saved to `output/` - downloadable
- **Knowledge Base**: Use `data/knowledge/` for all framework files
- **Batch Processing**: `data/syllabus/` used only for ZIP batch processing

