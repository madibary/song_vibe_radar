from typing import TypedDict, Dict, Any, NotRequired, List
from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage

class SongRecommendationsOutput(TypedDict):
    unsorted_songs: Dict[str, Dict[str, Any]]
    error: NotRequired[str]


class EvaluationNodeOutput(TypedDict):
    messages: List[BaseMessage]


class ModelEvaluationResult(TypedDict):
    score: float
    feedback: str


class ReferenceEvaluationOutput(TypedDict):
    messages: List[BaseMessage]




class VectorValidationOutput(TypedDict):
    unsorted_songs: Dict[str, Dict[str, Any]]
    best_match: NotRequired[Dict[str, Any]]
    sorted_songs: List[Dict[str, Any]]
