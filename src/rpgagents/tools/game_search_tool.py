"""Local game documentation search tool with optional caching"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import chromadb
import os
import logging

logger = logging.getLogger(__name__)

class GameSearchInput(BaseModel):
    game_name: str = Field(description="Full game name (e.g., 'Hollow Knight', 'Elden Ring')")
    query: str = Field(description="Search query about game mechanics, items, locations, etc.")


class GameSearchTool(BaseTool):
    name: str = "Search Game Information"
    description: str = (
        "Primary search tool. Searches both local documentation AND the web. "
        "Always use this tool for any game query. "
        "Input: 'game_name' (e.g. 'Hollow Knight') and 'query' (e.g. 'how to get void heart')."
    )
    args_schema: type[BaseModel] = GameSearchInput

    _chroma_client: chromadb.PersistentClient = PrivateAttr()
    _embeddings: object = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize ChromaDB
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self._chroma_client = chromadb.PersistentClient(path=db_path)

        # Initialize embeddings (using sentence-transformers for local, free embeddings)
        try:
            from chromadb.utils import embedding_functions
            self._embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            logger.warning(f"Failed to load embeddings: {e}")
            self._embeddings = None

    def _run(self, game_name: str, query: str) -> str:
        """Search indexed game documentation"""
        try:
            # Normalize to get game_id
            game_id = game_name
            normalized_game_id = game_id.lower().replace(" ", "_").replace("-", "_")
            collection_name = f"game_{normalized_game_id}"

            # Check if collection exists
            existing_collections = [c.name for c in self._chroma_client.list_collections()]
            
            # Helper to perform the search
            def perform_search(coll_name):
                 collection = self._chroma_client.get_collection(
                    name=coll_name,
                    embedding_function=self._embeddings
                )
                 result = collection.query(
                    query_texts=[query],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                 if result['distances'] and result['distances'][0]:
                     logger.info(f"🔍 Search Distances: {result['distances'][0]}")
                 return result

            if collection_name in existing_collections:
                results = perform_search(collection_name)
                
                # Lower distance = better match.
                # Threshold lowered to 0.45 to be stricter. 0.5-0.6 range was capturing loose matches.
                best_distance = results['distances'][0][0] if results['distances'] and results['distances'][0] else 1.0
                
                if best_distance > 0.45:
                    logger.warning(f"Local result relevance low (distance {best_distance:.4f} > 0.6). Triggering Web Search fallback.")
                    # Fall through to web search logic
                elif results['documents'] and results['documents'][0]:
                    # If we have good results, return them
                    formatted = []
                    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                        source = metadata.get('source', 'Local Cache')
                        formatted.append(f"**[Local Source {i}: {source}]**\n{doc}\n")
                    return "\n---\n".join(formatted)

            # --- Fallback: No local docs or no results found ---
            # Trigger web search
            logger.info(f"Checking web for '{game_id}'...")
            from rpgagents.tools.web_search_tool import WebSearchTool
            web_tool = WebSearchTool()
            
            # Use the original game_id (which might be "Hollow Knight") for web search
            web_results = web_tool.search(game_id, query)
            
            if not web_results:
                 return (
                    f"No local documentation indexed for '{normalized_game_id}' and web search returned no results. "
                    f"Available games: {', '.join([c.replace('game_', '') for c in existing_collections if c.startswith('game_')])}. "
                )

            # Index the found results
            docs_to_index = [r['content'] for r in web_results]
            sources_to_index = [r['href'] for r in web_results]
            
            logger.info(f"Indexing {len(docs_to_index)} new documents for {normalized_game_id}")
            self.index_documents(normalized_game_id, docs_to_index, sources_to_index)
            
            # Search again
            # We assume index_documents created the collection
            results = perform_search(collection_name)
            
            if not results['documents'] or not results['documents'][0]:
                 return "Indexed new content but search yielded no results. This is unexpected."

             # Format results from the new search
            formatted = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                source = metadata.get('source', 'Web Index')
                formatted.append(f"**[Web Index {i}: {source}]**\n{doc}\n")
            
            return "\n---\n".join(formatted)

        except Exception as e:
            logger.error(f"Local search error: {e}")
            import traceback
            traceback.print_exc()
            return f"Error searching local docs: {str(e)}. Use 'Web Search for Game Information' instead."

    def index_documents(self, game_id: str, documents: list[str], sources: list[str]) -> str:
        """Index documents for a game (for caching web results)"""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            game_id = game_id.lower().replace(" ", "_").replace("-", "_")
            collection_name = f"game_{game_id}"

            # Get or create collection
            collection = self._chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self._embeddings
            )

            # Split documents into chunks. 400 chars allows isolating specific items/paragraphs better than 1000.
            splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

            all_chunks = []
            all_metadatas = []
            all_ids = []

            for doc, source in zip(documents, sources):
                chunks = splitter.split_text(doc)
                for j, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadatas.append({"source": source, "game_id": game_id})
                    all_ids.append(f"{game_id}_{len(all_ids)}_{j}")

            if all_chunks:
                collection.add(
                    documents=all_chunks,
                    metadatas=all_metadatas,
                    ids=all_ids
                )

            return f"Indexed {len(all_chunks)} chunks for '{game_id}'"

        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return f"Error indexing: {str(e)}"

