import time
import logging
from helpers.formatter import parse_content
from models.description_generator import model
from langchain_core.messages import HumanMessage, SystemMessage
from state.node_outputs import DescriptionOutput
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

    ### INPUT DATA
    Reviews: {reviews}
    Lyrics: {lyrics}

    ### OUTPUT
    [Your 4-sentence description here]
    """

@traceable
def get_description(name, artist, reviews, lyrics) -> DescriptionOutput:
    user_input = f"Reviews: {reviews} \nLyrics: {lyrics}"
    time.sleep(2)
    try:
        response = model.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(content=user_input)
        ])

        content_str = str(response.content)
        description = parse_content(content_str)
        return {"description": description}
    except Exception as e:
        logger.exception("Error generating vibe description for %s by %s", name, artist)
        raise

