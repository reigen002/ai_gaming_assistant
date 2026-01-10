"""RPG Gaming Assistant Crew - Dynamic Multi-Game Support"""
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from rpgagents.tools.game_search_tool import GameSearchTool
from rpgagents.tools.web_search_tool import WebSearchTool
from typing import List
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()


@CrewBase
class Rpgagents:
    """RPG Gaming Assistant - Works with ANY RPG game dynamically"""

    # Construct absolute paths to config files
    agents_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'agents.yaml')
    tasks_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'tasks.yaml')

    # Declare agents and tasks lists (populated by decorators)
    agents: List[Agent] = []
    tasks: List[Task] = []

    def __init__(self, provider: str = "ollama"):
        # Initialize tools
        self._game_search_tool = GameSearchTool()
        self._web_search_tool = WebSearchTool()

        logger.info("✅ Tools initialized: Game Documentation Search, Web Search")
        
        # Load configs if they are strings (CrewAI decorator issue workaround)
        import yaml
        if isinstance(self.agents_config, str):
            with open(self.agents_config, 'r', encoding='utf-8') as f:
                self.agents_config = yaml.safe_load(f)
        
        if isinstance(self.tasks_config, str):
            with open(self.tasks_config, 'r', encoding='utf-8') as f:
                self.tasks_config = yaml.safe_load(f)

        # Get model based on provider
        if provider == "gemini":
            logger.info("🤖 Using LLM: Gemini 1.5 Flash (Fallback)")
            # Support both standard naming conventions
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            
            if not api_key:
                logger.warning("⚠️ GEMINI_API_KEY or GOOGLE_API_KEY not found. Fallback may fail.")
            
            # Pass the key explicitly to LiteLLM via environment variable override if needed, 
            # but usually passing api_key param is sufficient.
            self._llm = LLM(
                model="gemini/gemini-flash-latest",
                api_key=api_key
            )
        else:
            # Default to Ollama
            model_name = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

            logger.info(f"🤖 Using LLM: ollama/{model_name} at {ollama_host}")

            self._llm = LLM(
                model=f"ollama/{model_name}",
                base_url=ollama_host,
                temperature=0.3,
                max_tokens=2048,
            )

    @agent
    def researcher(self) -> Agent:
        """Research agent that searches for game information"""
        return Agent(
            config=self.agents_config['researcher'],
            # Only provide GameSearchTool to force the RAG/Indexing pipeline
            tools=[self._game_search_tool],
            llm=self._llm,
            verbose=True,
            max_iter=15,
            allow_delegation=False,
        )

    @agent
    def game_expert(self) -> Agent:
        """Expert agent that formats the guide"""
        return Agent(
            config=self.agents_config['game_expert'],
            llm=self._llm,
            verbose=True,
            max_iter=5,
            allow_delegation=False,
        )

    @task
    def research_task(self) -> Task:
        """Task to research game information"""
        return Task(
            config=self.tasks_config['research_task'],
        )

    @task
    def reporting_task(self) -> Task:
        """Task to create the final guide"""
        return Task(
            config=self.tasks_config['reporting_task'],
            context=[self.research_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RPG Gaming Assistant crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            cache=False,
            max_rpm=10,
        )

