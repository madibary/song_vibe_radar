# Song Vibe Radar

An agentic music discovery system that prioritizes the "vibes" of songs. Discover new music that matches the vibe of your favorite tracks!

## Description

This project allows users to input a reference song (by name and artist), and the system will:

1. Generate a detailed vibe description for the reference song.
2. Evaluate the description quality using an LLM-as-a-judge.
3. Find song recommendations.
4. Generate and evaluate vibe descriptions for each recommendation.
5. Sort recommendations based on vibe similarity using vector embeddings.
6. Output a sorted list of top songs that match the reference song's vibe.

## Features

- **Vibe-Based Discovery**: Focuses on emotional and atmospheric qualities rather than just genre or popularity.
- **Real-Time Evaluation**: Uses LLM-as-a-judge for quality assessment of vibe descriptions.
- **Vector Embeddings**: Employs semantic similarity for accurate vibe matching.
- **Agentic Architecture**: Built with LangGraph for robust, stateful processing.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/madibary/song_vibe_radar.git
   cd song_vibe_radar
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file):
   - `GROQ_API_KEY`: API key for Groq (used for vibe description generation).
   - `OPENROUTER_API_KEY`: API key for OpenRouter (used for evaluation).
   - `LAST_FM_API_KEY`: API key for Last.fm (used for song recommendations and validation).
   - `TAVILY_API_KEY`: API key for Tavily (used for web search).
   - `GENIUS_API_KEY`: API key for Genius (used for lyrics and song data).
   - `LOG_LEVEL` (optional): Logging level, defaults to "INFO".
   - `LOG_FILE` (optional): Log file path, defaults to "song_radar.log".

## Usage

Run the application:

```bash
python app.py
```

Enter the reference track name and artist when prompted. The system will process and output recommendations.

## How It Works

The system uses a graph-based architecture with the following components:

- **Nodes**: Handle specific tasks like song processing, vibe analysis, evaluation, and recommendations.
- **State Management**: Maintains context across processing steps.
- **Vector Validation**: Ensures vibe descriptions are semantically aligned.

## Project Structure

- `app.py`: Main entry point.
- `graphs/`: Contains the main graph and subgraphs.
- `nodes/`: Individual processing nodes.
- `models/`: AI models for description generation and evaluation.
- `state/`: State definitions.
- `tools/`: Utility tools.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
