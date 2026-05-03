from nodes.context_enricher import enrich_song
from state.subgraph_state import SubgraphState
from typing import cast
import logging

logger = logging.getLogger(__name__)


def process_song(state: SubgraphState) -> SubgraphState:
    song_data_only = state["song_data"][0]
    try:
        enriched_data = enrich_song(song_data_only)
        return cast(SubgraphState, {"song_data": [enriched_data]})
    except Exception as e:
        logger.exception("Error enriching song: %s by %s. error: %s", song_data_only.get('name'), song_data_only.get('artist'), e)
        raise
