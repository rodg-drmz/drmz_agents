# Verification Guide

## Quick Verification

Run the comprehensive verification script:

```bash
python scripts/verify_setup.py
```

This will test:
- ✅ CrewAI version (should be 1.6.0)
- ✅ Environment variables (DRMZ_OPENAI_API_KEY mapping)
- ✅ Agent configuration loading
- ✅ Knowledge Graph RAG tool
- ✅ Masumi task registry
- ✅ Morpheus crew initialization
- ✅ Chat interface setup

## Manual Verification Steps

### 1. Test CrewAI Version

```bash
python scripts/check_crewai_version.py
```

**Expected**: Should show CrewAI 1.6.0 installed and up to date.

### 2. Test Environment Variables

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DRMZ_OPENAI_API_KEY:', '✅ Set' if os.getenv('DRMZ_OPENAI_API_KEY') else '❌ Missing'); print('OPENAI_API_KEY:', '✅ Set' if os.getenv('OPENAI_API_KEY') else '⚠️  Will use DRMZ_OPENAI_API_KEY')"
```

**Expected**: Both should be set (OPENAI_API_KEY is auto-mapped from DRMZ_OPENAI_API_KEY).

### 3. Test Morpheus Chat

```bash
python src/drmz/morpheus_main.py --message "What is Ouroboros?"
```

**Expected**: 
- Should load knowledge sources (may show warnings for missing files - that's OK)
- Should create Morpheus agent
- Should execute chat and return a response about Ouroboros
- Response should be philosophical and reference Cardano/blockchain concepts

### 4. Test Knowledge Graph RAG

```bash
python -c "
from src.drmz.knowledge_graph.rag_tool import KnowledgeGraphRAGTool
tool = KnowledgeGraphRAGTool()
result = tool._run('Ouroboros')
print('✅ Knowledge Graph working!' if result else '❌ Empty result')
print(f'Result length: {len(result)} chars')
"
```

**Expected**: Should return graph query results about Ouroboros.

### 5. Test Masumi Task Registration

```bash
python scripts/register_morpheus_tasks.py
```

**Expected**: 
- Should register Morpheus tasks from tasks.yaml
- Should create `data/masumi/task_registry.json`
- Should export `data/masumi/masumi_tasks.json`
- Should show list of registered tasks

### 6. Test API Endpoints (if server is running)

```bash
# Start the API server first
# Then test:
curl http://localhost:8000/crew/agents/list
```

**Expected**: Should return JSON list of available agents.

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'drmz'"

**Solution**: Make sure you're running from project root and `src` is in Python path. The scripts handle this automatically.

### Issue: "OPENAI_API_KEY is required"

**Solution**: Check that `.env` file exists and has `DRMZ_OPENAI_API_KEY` set. The code auto-maps it to `OPENAI_API_KEY`.

### Issue: Knowledge source files not found

**Solution**: This is expected if files don't exist. The system will work with available files. Check `knowledge/` directory for actual files.

### Issue: Knowledge Graph RAG Tool errors

**Solution**: The tool is optional. If it fails, Morpheus will still work with standard knowledge sources.

## Success Criteria

✅ All verification tests pass  
✅ Morpheus chat returns responses  
✅ Knowledge sources load (even if some files are missing)  
✅ Masumi tasks can be registered  
✅ No critical errors in logs  

## Next Steps After Verification

1. **Test actual conversations**: Try different questions with Morpheus
2. **Register tasks**: Run the Masumi registration script
3. **Check logs**: Review any warnings (most are non-critical)
4. **Enhance knowledge graph**: Add more entities to the graph
5. **Integrate with drmz-app**: Test API endpoints from frontend

