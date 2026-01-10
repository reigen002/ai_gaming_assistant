# 🎮 RPG Gaming Assistant

**A Universal, Agentic Game Guide powered by RAG and Smart LLM Switching.**

> [!WARNING]
> **Construction in Progress**: This project is currently in **Active Development**. Features, APIs, and architectures are subject to breaking changes. Use with caution in production environments.

The **RPG Gaming Assistant** is an intelligent CLI tool designed to answer complex questions about *any* RPG game (Elden Ring, Hollow Knight, Dark Souls, etc.). It uses a multi-agent system (CrewAI) to research and write detailed guides, backed by a robust RAG (Retrieval-Augmented Generation) pipeline.


## ✨ Key Features

*   **Universal Game Support**: Can research and index information for any game on demand.
*   **🧠 Smart Provider Switching**:
    *   **Local First**: Automatically uses **Ollama (Llama 3.2)** when high-quality data is found in the local cache (Fast & Free).
    *   **Cloud Fallback**: Switches to **Gemini 1.5 Flash** when web search is required or local data is insufficient (High Intelligence).
*   **Self-Healing RAG Pipeline**:
    *   Scrapes game wikis and documentation.
    *   Optimizes data chunking (400 chars) for precise item retrieval.
    *   Filters false positives (Strict 0.45 semantic threshold).
*   **Multi-Agent Workflow**:
    *   **Research Agent**: Finds authoritative data locally or via the web.
    *   **Writer Agent**: Compiles findings into a structured, player-friendly guide.

## 🚀 Getting Started

### Prerequisites

| Requirement | Description |
| :--- | :--- |
| **Python** | v3.10 or higher |
| **Ollama** | Local LLM runner. [Download Here](https://ollama.com/) |
| **Gemini API Key** | For web search synthesis. [Get Key](https://aistudio.google.com/) |
| **Serper API Key** | For high-quality Google Search results. [Get Key](https://serper.dev/) |

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/reigen002/ai_gaming_assistant.git
    cd ai_gaming_assistant/backend/rpgagents
    ```

2.  **Install Dependencies**
    Using `uv` (recommended) or `pip`:
    ```bash
    pip install .
    # OR
    uv sync
    ```

3.  **Setup Environment**
    Create a `.env` file in the root directory:
    ```env
    # Required for Web Search Synthesis
    GEMINI_API_KEY=your_google_api_key_here
    SERPER_API_KEY=your_serper_api_key_here
    
    # Optional Overrides
    OLLAMA_MODEL=llama3.2:3b
    OLLAMA_HOST=http://localhost:11434
    CHROMA_DB_PATH=./chroma_db
    ```

4.  **Pull Local Model**
    Ensure your local Ollama instance has the model loaded:
    ```bash
    ollama pull llama3.2:3b
    ```

## 🎮 Usage

Run the main script to start the interactive assistant:

```bash
python src/rpgagents/main.py
```

### Example Workflow
1.  **Enter Game**: `Hollow Knight`
2.  **Enter Query**: `How to get the Map`
3.  **System Action**:
    *   *First Run*: Usage **Gemini** to scrape the web -> Indexes data -> Saves Guide.
    *   *Second Run*: Detects local data -> Uses **Ollama** (Free) -> Returns Guide instantly.

All generated guides are saved to the `output/` directory.


## 🧪 Validation

This project includes a full system validation suite to ensure reliability.
Run tests with:
```bash
python tests/full_system_validation.py
```

## 🤝 Contributing

Contributions are welcome! Please ensure any new features are covered by the validation script.

## ✍️ Author

*   **Reigen002** - *Initial work* - [GitHub Profile](https://github.com/reigen002)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Reigen002. All rights reserved.
