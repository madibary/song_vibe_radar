import time
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from models.description_generator import model
from helpers.formatter import parse_content

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
        content = parse_content(str(response.content))
        return content
    except Exception as e:
        print(f"Error refining vibe description for {name} by {artist}. Error: {e}")
        raise e