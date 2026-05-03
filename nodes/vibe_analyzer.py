import time
import logging
from langchain_core.messages import AIMessage
from models.description_generator import model
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

logger = logging.getLogger(__name__)

system_instructions = """
    ### ROLE
    You are a Music Ethnomusicologist and Sound Engineer. Your goal is to generate a standardized "Acoustic Fingerprint" description for a song based on its reviews and lyrics.

    ### TASK
    Write a dense, 4-sentence paragraph describing the song's sonic profile. Use the following strict format:
    1. Sentence 1: Emotional Vibe & Narrative. (How the song 'feels': "The mood is [Mood], evoking a sense of [Emotion]...")
    2. Sentence 2: The perfect environment or situation for the playing of the song. ("The song is perfect for [describe a mood or situation]") eg: "The song is perfect for a summer drive" or "The song is perfect for dancing in the club" or "The song is perfect for a quiet moment alone" etc.
    3. Sentence 3: Technical Genre & Tempo. (Focus on the musical genre and the general pace: "It is a [pace description] [genre] song...")
    4. Sentence 4: Instrumentation & Texture. (Focus on dominant instruments: "Characterized by [Instrument] and [Texture]...")

    
    ### CONSTRAINTS
    - Do NOT use the song title, artist name or song BPM in the description.
    - Do NOT use emojis, numbers or special symbols. 
    - Use objective descriptors (e.g., "reverberant," "distorted," "staccato") over subjective ones ("good," "great").
    - Maintain a clinical yet descriptive tone to ensure high-quality vector embeddings.
    - The paragraph length should be 55 to 75 words in total.
    - Do NOT specify the word count.


    ### OUTPUT
    [Your 4-sentence description here]
    """

@traceable
def get_description(name, artist, reviews, lyrics, recent_messages) -> AIMessage:
    user_input = ""
    if not recent_messages:
        user_input = f"Generate a new vibe description. Reviews: {reviews} \nLyrics: {lyrics}"
        recent_messages = [HumanMessage(content=user_input)]

    has_system_message = any(isinstance(m, SystemMessage) for m in recent_messages)
    if not has_system_message:
        recent_messages = [SystemMessage(content=system_instructions), *recent_messages]

    time.sleep(2)
    try:
        response = model.invoke([
            *recent_messages
        ])
        return response
    except Exception as e:
        logger.exception("Error generating vibe description for %s by %s: %s", name, artist, str(e))
        return AIMessage(content="")  # Return an empty description on failure

