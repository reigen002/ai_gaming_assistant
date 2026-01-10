
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from rpgagents.tools.game_search_tool import GameSearchTool, GameSearchInput
from rpgagents.tools.web_search_tool import WebSearchTool
from rpgagents.crew import Rpgagents
from rpgagents.main import determine_provider_and_search

class TestSystemValidation(unittest.TestCase):

    def setUp(self):
        # Ensure environment variables are set for testing
        os.environ["CHROMA_DB_PATH"] = "./tests/chroma_db_validation"
        os.environ["GEMINI_API_KEY"] = "fake_key_for_validation" # We mock the calls mostly
        os.environ["GOOGLE_API_KEY"] = "fake_key_for_validation"

    def test_01_tool_registration(self):
        """Verify tools are correctly registered and args_schema works"""
        tool = GameSearchTool()
        self.assertEqual(tool.name, "Search Game Information")
        self.assertTrue(issubclass(tool.args_schema, GameSearchInput))
        
        # Validate input schema
        valid_input = {"game_name": "Test Game", "query": "Test Query"}
        tool.args_schema(**valid_input) # Should not raise

    def test_02_smart_switching_logic_local(self):
        """Verify determine_provider_and_search returns 'ollama' for Local Source"""
        
        with patch('rpgagents.tools.game_search_tool.GameSearchTool._run') as mock_run:
            mock_run.return_value = "**[Local Source 1: Cache]**\nSome content"
            
            provider, result = determine_provider_and_search("Hollow Knight", "Void Heart")
            
            self.assertEqual(provider, "ollama")
            self.assertIn("Local Source", result)

    def test_03_smart_switching_logic_web(self):
        """Verify determine_provider_and_search returns 'gemini' for Web Index"""
        
        with patch('rpgagents.tools.game_search_tool.GameSearchTool._run') as mock_run:
            mock_run.return_value = "**[Web Index 1: URL]**\nSome content"
            
            provider, result = determine_provider_and_search("Elden Ring", "Malenia")
            
            self.assertEqual(provider, "gemini")
            self.assertIn("Web Index", result)

    def test_04_agent_initialization(self):
        """Verify RAG agents initialize with correct LLM config"""
        
        # Test Default (Ollama)
        crew_default = Rpgagents(provider="ollama")
        self.assertTrue(crew_default._llm.model.startswith("ollama"))
        
        # Test Gemini
        crew_gemini = Rpgagents(provider="gemini")
        self.assertTrue(crew_gemini._llm.model.startswith("gemini"))

    @patch('rpgagents.tools.web_search_tool.WebSearchTool.search') 
    @patch('rpgagents.tools.game_search_tool.GameSearchTool.index_documents')
    def test_05_rag_pipeline_integration(self, mock_index, mock_web_search):
        """Verify GameSearchTool falls back to WebSearchTool correctly"""
        
        # setup mock for web search
        mock_web_search.return_value = [
            {"title": "Test Page", "href": "http://test.com", "content": "The answer is 42."}
        ]
        
        tool = GameSearchTool()
        # Mock internal ChromaDB client to return empty collection list to trigger fallback
        tool._chroma_client.list_collections = MagicMock(return_value=[])
             
        result = tool._run("New Game", "What is the answer?")
             
        # Assert web search was called with ORIGINAL game name (not normalized)
        mock_web_search.assert_called_with("New Game", "What is the answer?")
             
        # Assert indexing was called
        mock_index.assert_called()


if __name__ == '__main__':
    print("🚀 Starting End-to-End System Validation...")
    unittest.main(verbosity=2)
