from typing import List, Union
from pydantic import BaseModel

from ..event_factory.constants import PossibleEvent, Storyline
from ..agent.base import PRResponse, AdjudicatorResponse, RouterResponse


class LogEntry(BaseModel):
    turn: int
    router_response: Union[RouterResponse, None]
    event: PossibleEvent
    private_fact_ids: List[str]
    public_fact_ids: List[str]
    response: PRResponse
    adjudicator_response: AdjudicatorResponse
    stock_price: float
    public_trust: int

class CrisisLog(BaseModel):
    agent_model: str
    crisis_setup: Storyline
    initial_stock_price: float
    initial_public_trust: int
    turns: List[LogEntry]
