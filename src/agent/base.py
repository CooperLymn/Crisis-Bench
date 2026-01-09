from pydantic import BaseModel
from typing import Union, List


class PRResponse(BaseModel):
    situation_analysis: str
    strategic_intent: str
    internal_thought: str
    public_statement: str
    revealed_fact_ids: Union[List[str], str]

class AdjudicatorResponse(BaseModel):
    severity: float
    evidence_level: float
    accountability: int
    transparency: int
    empathy: int
    costly_signaling: int

class RouterResponse(BaseModel):
    reasoning: str
    selected_event_id: str
