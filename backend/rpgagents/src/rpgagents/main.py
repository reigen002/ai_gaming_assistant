"""RPG Gaming Assistant - Dynamic Multi-Game Support"""
import sys
import os
import warnings
import logging
from datetime import datetime

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger(__name__)

from rpgagents.crew import Rpgagents
from rpgagents.tools.game_search_tool import GameSearchTool


def direct_search(game_name: str, query: str) -> str:
    """Direct search using GameSearchTool - NO LLM CALLS (faster, free)"""
    try:
        tool = GameSearchTool()
        return tool._run(game_name=game_name, query=query)
    except Exception as e:
        return f"Search error: {str(e)}"


def run():

    """Interactive mode - ask user for game and query"""
    print("\n" + "=" * 70)
    print("🎮 RPG GAMING ASSISTANT - Universal Game Guide")
    print("=" * 70)
    print("Supports ANY RPG game: Hollow Knight, Elden Ring, Dark Souls,")
    print("Skyrim, Baldur's Gate 3, and many more!")
    print("=" * 70)

    # Get game name
    game_name = input(
        "\n📌 Enter the game name (e.g., 'Hollow Knight', 'Elden Ring'): "
    ).strip().replace('\ufeff', '')

    if not game_name:
        print("❌ Game name is required.")
        return 1

    # Get query
    print(f"\n💡 Example queries for {game_name}:")
    print("   - Where to find [item name]")
    print("   - How to defeat [boss name]")
    print("   - Best build for [class/playstyle]")
    print("   - Location of [area/NPC]")

    query = input(f"\n❓ What would you like to know about {game_name}? ").strip().replace('\ufeff', '')

    if not query:
        print("❌ Query is required.")
        return 1

    print(f"\n🔍 Searching: '{query}' for {game_name}...")
    print("=" * 70 + "\n")

    inputs = {
        'game_name': game_name,
        'query': query,
        'current_year': str(datetime.now().year)
    }

    try:
        # --- SMART PROVIDER SWITCHING ---
        # 1. Perform a pre-search to determine if data is local or requires web
        print(f"\n🔍 Checking knowledge base for query...")
        
        # Extracted logic for readability and testing
        # --- CLOUD-ONLY MODE ---
        # We now rely on the Agent to perform the search using its tools.
        print(f"\n🚀 Starting Agent Crew (Cloud-Only)...")
        
        # Initialize with default (Gemini)
        rpg_agents = Rpgagents()
        result = rpg_agents.crew().kickoff(inputs=inputs)
        result_text = result.raw if hasattr(result, 'raw') else str(result)
                         
        print("\n" + "=" * 70)
        print("📖 YOUR GAME GUIDE")
        print("=" * 70)
        print(result_text)
        print("=" * 70)

        # Save to file in root 'output' folder
        # Determine path helper: src/rpgagents/main.py -> backend/rpgagents/output
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
        output_dir = os.path.join(project_root, 'output')
        
        os.makedirs(output_dir, exist_ok=True)

        filename = f"guide_{game_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
        print(f"\n💾 Guide saved to: {file_path}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def crew_search(game_name: str, query: str):
    """Primary method: Use crew with LLM for formatted responses"""
    inputs = {
        'game_name': game_name,
        'query': query,
        'current_year': str(datetime.now().year)
    }
    try:
        result = Rpgagents().crew().kickoff(inputs=inputs)
        return result.raw if hasattr(result, 'raw') else str(result)
    except Exception as e:
        error_msg = str(e)
        # Check for rate limit error
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            logger.warning(f"⚠️ Rate limit hit, falling back to direct search (no LLM): {error_msg}")
            return direct_search(game_name, query)
        raise


def quick_search(game_name: str, query: str):
    """Programmatic search - tries crew first (with LLM), falls back to direct search on rate limit"""
    try:
        return crew_search(game_name, query)
    except Exception as e:
        logger.warning(f"Crew search failed: {str(e)}, falling back to direct search")
        return direct_search(game_name, query)


def start_api(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI server"""
    import uvicorn
    from rpgagents.api import app
    
    print(f"🚀 Starting RPG Gaming Assistant API on {host}:{port}")
    print(f"📖 API Docs available at http://{host}:{port}/docs")
    print(f"📊 ReDoc available at http://{host}:{port}/redoc")
    
    uvicorn.run(app, host=host, port=port, reload=False)


def train():
    """Train the crew for a given number of iterations."""
    inputs = {
        "game_name": "Hollow Knight",
        "query": "How to get the Mantis Claw",
        'current_year': str(datetime.now().year)
    }
    try:
        Rpgagents().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )
        return 0
    except Exception as e:
        print(f"❌ Training error: {e}")
        return 1


def replay():
    """Replay the crew execution from a specific task."""
    try:
        Rpgagents().crew().replay(task_id=sys.argv[1])
        return 0
    except Exception as e:
        print(f"❌ Replay error: {e}")
        return 1


def test():
    """Test the crew with sample queries."""
    test_cases = [
        ("Hollow Knight", "Where to find Mantis Claw"),
        ("Elden Ring", "Best staff for sorcerer build"),
        ("Dark Souls 3", "How to defeat Nameless King"),
    ]

    print("🧪 Running test cases...\n")

    for game, query in test_cases:
        print(f"Testing: {game} - {query}")
        try:
            result = quick_search(game, query)
            print(f"✅ Success - {len(result)} characters")
        except Exception as e:
            print(f"❌ Failed: {e}")
        print("-" * 50)

    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "api":
            start_api()
        elif command == "train":
            sys.exit(train())
        elif command == "replay":
            sys.exit(replay())
        elif command == "test":
            sys.exit(test())
        else:
            print(f"Unknown command: {command}")
            print("Available commands: api, train, replay, test")
            sys.exit(1)

    sys.exit(run())

