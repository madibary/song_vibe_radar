"""Basic tests for Song Vibe Radar."""
import pytest
from state.agent_state import AgentState

def test_imports():
    """Test that all main modules can be imported."""
    try:
        from graphs.main_graph import graph
        from nodes.validate_song import validate_song
        from models.description_generator import model
        from helpers.formatter import parse_content
        assert True  # If we get here, imports worked
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_helper_functions():
    """Test helper functions work."""
    from helpers.formatter import parse_content

    # Test normal content
    content = "This is normal content"
    assert parse_content(content) == content

    # Test content with think tags
    think_content = "<think>reasoning</think>Actual content"
    assert parse_content(think_content) == "Actual content"


def test_parse_content_unclosed_think_tag():
    from helpers.formatter import parse_content
    result = parse_content("<think>some reasoning without closing tag")
    assert result == "some reasoning without closing tag"


def test_parse_content_empty_string():
    from helpers.formatter import parse_content
    assert parse_content("") == ""


def test_parse_content_whitespace_stripped():
    from helpers.formatter import parse_content
    result = parse_content("<think>reasoning</think>   trimmed   ")
    assert result == "trimmed"


def test_map_songs_returns_end_when_empty():
    from nodes.map_songs import map_songs
    from langgraph.graph import END
    assert map_songs({"unsorted_songs": {}}) == END


def test_map_songs_returns_end_when_key_missing():
    from nodes.map_songs import map_songs
    from langgraph.graph import END
    assert map_songs({}) == END


def test_map_songs_returns_one_send_per_song():
    from nodes.map_songs import map_songs
    from langgraph.types import Send
    state = {
        "unsorted_songs": {
            "s1": {"id": "s1", "name": "Song A", "artist": "Artist A"},
            "s2": {"id": "s2", "name": "Song B", "artist": "Artist B"},
        }
    }
    result = map_songs(state)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(s, Send) for s in result)


def test_generate_response_text_approved():
    from nodes.evaluation import generate_response_text, ModelEvaluationOutput
    response = ModelEvaluationOutput(score=9.0, feedback="Excellent")
    result = generate_response_text(response, 8.0)
    assert "APPROVED" in result
    assert "9.0" in result


def test_generate_response_text_retry():
    from nodes.evaluation import generate_response_text, ModelEvaluationOutput
    response = ModelEvaluationOutput(score=5.0, feedback="Too generic")
    result = generate_response_text(response, 8.0)
    assert "Retry" in result
    assert "Too generic" in result


def test_generate_response_text_at_threshold_passes():
    from nodes.evaluation import generate_response_text, ModelEvaluationOutput
    response = ModelEvaluationOutput(score=8.0, feedback="Good enough")
    result = generate_response_text(response, 8.0)
    assert "APPROVED" in result


def test_reduce_enrichment_merges_fields():
    from nodes.reduce_songs import reduce_enrichment_data
    state = {
        "unsorted_songs": {
            "t1": {"id": "t1", "name": "Song A", "artist": "Artist A"},
            "t2": {"id": "t2", "name": "Song B", "artist": "Artist B"},
        },
        "song_data": [
            {"id": "t1", "vibe_description": "Energetic and raw", "lyrics": "La la la"},
        ],
    }
    result = reduce_enrichment_data(state)
    assert result["unsorted_songs"]["t1"]["vibe_description"] == "Energetic and raw"
    assert result["unsorted_songs"]["t1"]["name"] == "Song A"
    assert result["unsorted_songs"]["t2"]["name"] == "Song B"
    assert "vibe_description" not in result["unsorted_songs"]["t2"]


def test_reduce_enrichment_does_not_mutate_original():
    from nodes.reduce_songs import reduce_enrichment_data
    original = {"id": "t1", "name": "Song A"}
    state = {
        "unsorted_songs": {"t1": original},
        "song_data": [{"id": "t1", "lyrics": "some lyrics"}],
    }
    reduce_enrichment_data(state)
    assert "lyrics" not in original


