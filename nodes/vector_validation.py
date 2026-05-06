from state.agent_state import AgentState
from typings.node_outputs import VectorValidationOutput
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

_embeddings_model = None


def _get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return _embeddings_model


def validate_by_vectors(state: AgentState) -> VectorValidationOutput:
    reference_track = state["reference_track"]
    first_song_desc = str(reference_track.get("vibe_description"))
    logger.info("First song description: %s", first_song_desc)
    first_song_vector = _get_embeddings_model().encode(first_song_desc)

    highest_song_desc_id = None
    highest_score = 0.0

    songs = state.get("unsorted_songs", {}).copy()
    unsorted_list = []

    for song_id in state.get("unsorted_songs", {}):
        song_data = state["unsorted_songs"][song_id]
        unsorted_list.append(song_data)
        try:
            if song_data.get("vibe_description") is None:
                songs[song_id]["score"] = 0
                logger.info("No vibe description for %s by %s, skipping vector validation.", song_data.get('name'), song_data.get('artist'))
                continue
            embedding = _get_embeddings_model().encode(song_data["vibe_description"])
            similarity_raw = _get_embeddings_model().similarity(first_song_vector, embedding)
            try:
                similarity_val = float(similarity_raw)
            except Exception:
                # fallback value if conversion fails
                similarity_val = 0.0
            songs[song_id]["score"] = similarity_val
            if similarity_val > highest_score:
                highest_song_desc_id = song_id
                highest_score = similarity_val
        except Exception as e:
            logger.exception("Failed to create encoding for %s by %s. Error: %s", song_data.get('name'), song_data.get('artist'), e)

    best_match = state["unsorted_songs"].get(highest_song_desc_id)
    sorted_songs = sorted(unsorted_list, key=lambda x: x.get('score', 0), reverse=True)
    for index, song in enumerate(sorted_songs):
        logger.info("%d. %s by %s. Score: %s", index + 1, song.get('name'), song.get('artist'), song.get('score'))
        logger.debug("vibe description: %s\n", song.get("vibe_description", "No vibe description available"))
    result = {"unsorted_songs": songs, "sorted_songs": sorted_songs}
    if best_match is not None:
        result["best_match"] = best_match
    from typing import cast
    return cast(VectorValidationOutput, result)

