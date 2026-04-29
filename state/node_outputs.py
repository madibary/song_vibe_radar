from typing import TypedDict, Dict, Any, NotRequired, List
from langchain_core.messages import BaseMessage


class SongRecommendationsOutput(TypedDict):
    unsorted_songs: Dict[str, Dict[str, Any]]
    error: NotRequired[str]


class EvaluationOutput(TypedDict):
    messages: List[BaseMessage]


class ReferenceEvaluationOutput(TypedDict):
    reference_critique: str


class DescriptionOutput(TypedDict):
    description: str


class VectorValidationOutput(TypedDict):
    unsorted_songs: Dict[str, Dict[str, Any]]
    best_match: NotRequired[Dict[str, Any]]
    sorted_songs: List[Dict[str, Any]]
