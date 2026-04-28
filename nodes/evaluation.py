
from langchain_core.messages import HumanMessage, SystemMessage
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from models.evaluation import model



system_instructions = """
    ### ROLE
    You are a strict musicologist. Your goal is to review a song's vibe description. 

    ### CRITERIA
    1. Uniqueness: Mood/energy must not be generic.
    2. Objectivity: Uses objective descriptors.

    ### OUTPUT RULES
    - If all criteria pass: Reply with "APPROVED" and nothing else.
    - If any criteria fail: Provide a critique (max 30 words).
    - NEVER state the numerical word count in your final response.

    ### INPUT DATA
    Vibe Description: {vibe_description}

    ### OUTPUT
    [Your critique or "APPROVED" here]
"""


def evaluate_vibe_description(state: SubgraphState):
    song = state["song_data"][0]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Vibe Description: {song['vibe_description']}")
    recent_messages = state["messages"][-6:]  # Only send the last 6 messages to keep it clean
    try:
        response = model.invoke([
        system_prompt,
        song_context,
        *recent_messages
        ])
        return {"messages": [response]}

    except Exception as e:
        print(f"Error evaluating description of {song['name']} by {song['artist']}: {e}")
        #raise e
        return ""

def evaluate_reference_vibe_description(state: AgentState):
    song = state["reference_track"]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Vibe Description: {song['vibe_description']}")
    try:
        response = model.invoke([
        system_prompt,
        song_context
        ])
        return {"reference_critique": response.content}

    except Exception as e:
        print(f"Error evaluating description of {song['name']} by {song['artist']}: {e}")
        #raise e
        return ""