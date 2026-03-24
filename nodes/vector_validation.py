from state.agent_state import AgentState
from sentence_transformers import SentenceTransformer

from nodes.vibe_analyzer import get_description

embeddings_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

def validate_by_vectors(state: AgentState):
    reference_track = state["reference_track"]
    response = get_description(reference_track["name"], reference_track["artist"], reference_track["reviews"], reference_track["lyrics"])
    first_song_desc = response["description"]
    first_song_vector = embeddings_model.encode(first_song_desc)
    highest_song_desc_id = None
    highest_score = 0

    songs = state["unsorted_songs"].copy()
    unsorted_list = []
    
    print(f"First song description: {first_song_desc}")
    for song_id in state["unsorted_songs"]:
        song_data = state["unsorted_songs"][song_id]
        unsorted_list.append(song_data)
        try:
            if (song_data).get("vibe_description") is None:
                songs[song_id]["score"] = 0
                print(f"No vibe description for {song_data['name']} by {song_data['artist']}, skipping vector validation.")
                continue
            embedding = embeddings_model.encode(song_data["vibe_description"])
            similarity = embeddings_model.similarity(first_song_vector, embedding)
            songs[song_id]["score"] = similarity
            if (similarity > highest_score):
                highest_song_desc_id = song_id
                highest_score = similarity
        except Exception as e:
            print (f"Failed to create encoding for {song_data["name"]} by {song_data["artist"]}. Error: {e}")

    best_match = state["unsorted_songs"][highest_song_desc_id]
    sorted_songs = sorted(unsorted_list, key=lambda x: x['score'], reverse=True)
    print(f"Best match: {best_match["name"]} by {best_match["artist"]}.\n vibe:{best_match["vibe_description"]} \n")
    for index, song in enumerate(sorted_songs):
        print(f"{index+1}. {song["name"]} by {song["artist"]}. Score: {song["score"]}")
    return {"unsorted_songs": songs, "best_match": best_match, "sorted_songs": sorted_songs}

