
import time

from langsmith import traceable
from helpers.formatter import get_content_only
from models.description_generator import model
from langchain_core.messages import HumanMessage, SystemMessage

from state.subgraph_state import SubgraphState

system_instructions = """
### REFINEMENT TASK
You are a precision editor. You previously generated a song vibe description that was rejected by the Musicologist Judge. 

### ORIGINAL VERSION
{original_description}

### CRITIQUE RECEIVED
{judge_critique}

### REFINEMENT RULES
1. **Preserve the Core:** Keep the unique mood and energy identified in the original.
2. **Apply Corrections:** Address every specific failure point mentioned in the critique.
3. **Hard Constraints:** - Word count MUST be between 55 and 75. 
   - Use objective technical descriptors (e.g., "staccato," "reverb-heavy," "syncopated").
    - Maintain the 4-sentence structure.

### OUTPUT
Provide only the refined description. Do not include introductory text like "Here is the revised version."""

@traceable
def get_refined_description(name, artist, vibe_description, critique) -> str:
    user_input = f"original description: {vibe_description}\nJudge critique: {critique}"
    time.sleep(2)
    try:
        response = model.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(content=user_input)
        ])
        # remove reasoning from the model's response if it includes a <think>...</think> block, leaving only the content
        content = get_content_only(str(response.content))
        return content
    except Exception as e:
        print(f"Error refining vibe description for {name} by {artist}. Error: {e}")
        raise e

def refine_vibe(state: SubgraphState):
    song_data = state["song_data"][0].copy()
    critique = state["messages"][-1].content if state["messages"] else ""
    print(f"\n\nREFINING vibe description for {song_data['name']}")
    print(f"Original description for {song_data['name']}: {song_data['vibe_description']}")
    print(f"Critique received for {song_data['name']}: {critique}")
    try:
        response = get_refined_description(song_data["name"], song_data["artist"], song_data["vibe_description"], critique)
        print(f"Refined description for {song_data['name']}: {response}")
        song_data["vibe_description"] = response
        return {"song_data": [song_data], "iterations": state["iterations"] + 1, "critique": critique}
    except Exception as e:
        print(f"Error refining vibe description of {song_data['name']} by {song_data['artist']}: {e}")
        raise e
