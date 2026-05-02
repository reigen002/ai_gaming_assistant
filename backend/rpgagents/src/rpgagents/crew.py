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

    def __init__(self):
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

        # Standardizing on Gemini (Cloud-Only)
        logger.info("🤖 Using LLM: Gemini Flash Latest (Cloud Only)")
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found. Agent execution may fail.")
        
        self._llm = LLM(
            model="gemini/gemini-flash-latest",
            api_key=api_key,
            temperature=0.3
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
        """Task to create the final guide - ENABLED for full formatting"""
        return Task(
            config=self.tasks_config['reporting_task'],
            context=[self.research_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RPG Gaming Assistant crew - Full setup with both agents"""
        return Crew(
            agents=self.agents,  # Both researcher and game_expert
            tasks=self.tasks,  # Both research and reporting tasks
            process=Process.sequential,
            verbose=True,
            memory=False,
            cache=False,
            max_rpm=100,
        )

