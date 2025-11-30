"""
Knowledge Graph RAG Tool for Morpheus
Provides semantic retrieval from the knowledge graph to enhance RAG capabilities.
"""

import json
import os
from typing import List, Dict, Optional, Any, Type
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class KnowledgeGraphRAGToolInput(BaseModel):
    """Input schema for KnowledgeGraphRAGTool."""
    query: str = Field(..., description="The search query to find relevant entities and relationships in the knowledge graph.")


class KnowledgeGraphRAGTool(BaseTool):
    """
    Tool that queries the knowledge graph to retrieve relevant entities and relationships
    for enhanced RAG retrieval in Morpheus conversations.
    """
    
    name: str = "Knowledge Graph RAG Tool"
    description: str = """
    Queries the knowledge graph to find relevant concepts, entities, and relationships
    based on a user's question. Returns structured information that can be used to
    enhance context for Morpheus responses.
    
    Use this tool when:
    - User asks about Cardano concepts, governance, or Web3 topics
    - You need to find related entities or relationships
    - You want to provide contextually rich responses with graph-based knowledge
    """
    args_schema: Type[BaseModel] = KnowledgeGraphRAGToolInput
    
    def __init__(self, graph_dir: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        if graph_dir is None:
            # Default to project knowledge_graph directory
            base = Path(__file__).resolve().parents[2]
            graph_dir = str(base / "src" / "drmz" / "knowledge_graph")
        
        # Store as instance variables (not Pydantic fields)
        self._graph_dir = Path(graph_dir)
        self._nodes_path = self._graph_dir / "nodes.json"
        self._edges_path = self._graph_dir / "edges.json"
        self._schema_path = self._graph_dir / "schema.json"
        
        # Load graph data
        self._nodes = self._load_nodes()
        self._edges = self._load_edges()
        self._schema = self._load_schema()
    
    def _load_nodes(self) -> List[Dict]:
        """Load nodes from JSON file."""
        if not self._nodes_path.exists():
            return []
        try:
            with open(self._nodes_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading nodes: {e}")
            return []
    
    def _load_edges(self) -> List[Dict]:
        """Load edges from JSON file."""
        if not self._edges_path.exists():
            return []
        try:
            with open(self._edges_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading edges: {e}")
            return []
    
    def _load_schema(self) -> Dict:
        """Load schema from JSON file."""
        if not self._schema_path.exists():
            return {}
        try:
            with open(self._schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading schema: {e}")
            return {}
    
    def _search_nodes(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search nodes by name or attributes matching the query.
        Simple text matching - can be enhanced with embeddings later.
        """
        query_lower = query.lower()
        matches = []
        
        for node in self._nodes:
            # Match by name
            if query_lower in node.get("name", "").lower():
                matches.append(node)
                continue
            
            # Match by type
            if query_lower in node.get("type", "").lower():
                matches.append(node)
                continue
            
            # Match in attributes
            attrs = node.get("attributes", {})
            for key, value in attrs.items():
                if query_lower in str(value).lower():
                    matches.append(node)
                    break
        
        return matches[:limit]
    
    def _get_related_entities(self, node_id: str, depth: int = 2) -> Dict[str, List[Dict]]:
        """
        Get entities related to a given node through edges.
        Returns a dict with 'incoming' and 'outgoing' relationships.
        """
        related = {"incoming": [], "outgoing": []}
        
        for edge in self._edges:
            if edge["source"] == node_id:
                # Find target node
                target = next((n for n in self._nodes if n["id"] == edge["target"]), None)
                if target:
                    related["outgoing"].append({
                        "node": target,
                        "relationship": edge["type"]
                    })
            
            if edge["target"] == node_id:
                # Find source node
                source = next((n for n in self._nodes if n["id"] == edge["source"]), None)
                if source:
                    related["incoming"].append({
                        "node": source,
                        "relationship": edge["type"]
                    })
        
        return related
    
    def _search_filesystem(self, query: str, limit: int = 5) -> str:
        """
        Search filesystem knowledge base for relevant content.
        Searches in data/knowledge/ directory.
        """
        import os
        from pathlib import Path
        
        # Find knowledge directory
        base = Path(__file__).resolve().parents[2]
        knowledge_dir = base / "data" / "knowledge"
        
        if not knowledge_dir.exists():
            return ""
        
        query_lower = query.lower()
        # Extract key terms from query (remove common words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "from", "using", "method", "for", "on", "about"}
        query_terms = [w for w in query_lower.split() if w not in stop_words and len(w) > 2]
        
        # If query is very specific, also try broader terms
        # For example, "Socratic method for debates" -> also search for "Socratic", "debates", "method"
        if len(query_terms) > 3:
            # Keep the most important terms (longer words, not common verbs)
            important_terms = [t for t in query_terms if len(t) > 4 or t in ["game", "gamification", "pbl", "sel", "udl", "crt"]]
            if important_terms:
                query_terms = important_terms
        
        if not query_terms:
            query_terms = query_lower.split()
        
        results = []
        seen_files = set()
        
        # Search all markdown and text files
        for ext in ["*.md", "*.txt"]:
            for file_path in knowledge_dir.rglob(ext):
                # Skip README files
                if "README" in file_path.name.upper():
                    continue
                    
                if str(file_path) in seen_files:
                    continue
                seen_files.add(str(file_path))
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    content_lower = content.lower()
                    
                    # Check if any query terms match
                    matches = sum(1 for term in query_terms if term in content_lower)
                    
                    if matches > 0:
                        # Extract relevant sections
                        lines = content.split('\n')
                        relevant_lines = []
                        
                        # Find lines with matches and include context
                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            if any(term in line_lower for term in query_terms):
                                # Include context (3 lines before and after)
                                start = max(0, i - 3)
                                end = min(len(lines), i + 4)
                                context = lines[start:end]
                                relevant_lines.extend(context)
                                
                                # Add separator between sections
                                if relevant_lines and relevant_lines[-1] != "---":
                                    relevant_lines.append("---")
                                
                                if len('\n'.join(relevant_lines)) > 1500:
                                    break
                        
                        if relevant_lines:
                            # Remove duplicates while preserving order
                            seen_lines = set()
                            unique_lines = []
                            for line in relevant_lines:
                                line_stripped = line.strip()
                                if line_stripped and line_stripped not in seen_lines:
                                    seen_lines.add(line_stripped)
                                    unique_lines.append(line)
                            
                            results.append({
                                "file": file_path.name,
                                "path": str(file_path.relative_to(knowledge_dir)),
                                "content": '\n'.join(unique_lines[:30]),  # Limit to 30 lines
                                "score": matches
                            })
                            
                            if len(results) >= limit:
                                break
                except Exception as e:
                    continue
            
            if len(results) >= limit:
                break
        
        if not results:
            return ""
        
        # Sort by score (number of matches)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Format results
        formatted = []
        for r in results[:limit]:
            formatted.append(f"📄 {r['path']}\n{r['content']}")
        
        return "\n\n".join(formatted)
    
    def _run(self, query: str) -> str:
        """
        Execute the knowledge graph query.
        Returns formatted string with relevant graph information.
        """
        results = []
        
        # First, try knowledge graph search
        if self._nodes:
            matching_nodes = self._search_nodes(query, limit=5)
            
            if matching_nodes:
                result_parts = []
                result_parts.append(f"Found {len(matching_nodes)} relevant entities in knowledge graph:\n")
                
                for node in matching_nodes:
                    result_parts.append(f"\n📌 {node.get('name', 'Unknown')} ({node.get('type', 'Unknown')})")
                    
                    # Add attributes if available
                    attrs = node.get("attributes", {})
                    if attrs:
                        attr_str = ", ".join(f"{k}: {v}" for k, v in attrs.items())
                        result_parts.append(f"   Attributes: {attr_str}")
                    
                    # Get related entities
                    related = self._get_related_entities(node["id"])
                    
                    if related["outgoing"]:
                        result_parts.append(f"   Related concepts:")
                        for rel in related["outgoing"][:3]:
                            result_parts.append(
                                f"     → {rel['node']['name']} ({rel['relationship']})"
                            )
                
                results.append("\n".join(result_parts))
        
        # Also search filesystem knowledge base
        filesystem_results = self._search_filesystem(query, limit=3)
        if filesystem_results:
            results.append(f"\n--- Filesystem Knowledge Base ---\n{filesystem_results}")
        
        if not results:
            return f"No matching information found for query: '{query}'. Try different keywords or add knowledge to the knowledge base."
        
        return "\n\n".join(results)
    
    def get_context_for_query(self, query: str, max_nodes: int = 5) -> Dict[str, Any]:
        """
        Get structured context for a query that can be used in RAG.
        Returns a dict with nodes, edges, and formatted text.
        """
        matching_nodes = self._search_nodes(query, limit=max_nodes)
        
        context = {
            "query": query,
            "nodes": matching_nodes,
            "relationships": [],
            "formatted_text": ""
        }
        
        # Collect relationships
        node_ids = {node["id"] for node in matching_nodes}
        for edge in self._edges:
            if edge["source"] in node_ids or edge["target"] in node_ids:
                context["relationships"].append(edge)
        
        # Build formatted text
        if matching_nodes:
            context["formatted_text"] = self._run(query)
        
        return context

