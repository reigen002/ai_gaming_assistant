from celery import Celery
from rpgagents.crew import Rpgagents
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery
# Use 'redis://localhost:6379/0' as the default broker
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery("rpgagents", broker=redis_url, backend=redis_url)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
)

@app.task(bind=True)
def run_crew_task(self, game_name, query):
    """
    Background task to run the CrewAI pipeline.
    """
    try:
        self.update_state(state='PROGRESS', meta={'message': 'Summoning Agents...'})
        
        inputs = {
            'game_name': game_name,
            'query': query,
            'current_year': '2026'
        }
        
        rpg_agents = Rpgagents()
        result_obj = rpg_agents.crew().kickoff(inputs=inputs)
        
        final_answer = result_obj.raw if hasattr(result_obj, 'raw') else str(result_obj)
        
        return {
            'game': game_name,
            'query': query,
            'result': final_answer
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e
