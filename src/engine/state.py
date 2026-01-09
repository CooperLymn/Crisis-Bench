import json
from pydantic import BaseModel
from typing import Dict, List, Set, Literal

from ..agent.base import PRResponse
from ..event_factory.constants import Storyline, InitialState, PossibleEvent, EventTypeLiteral


class ScoredResponse(BaseModel):
    text: str
    accountability: float
    transparency: float
    empathy: float
    costly_signaling: float

class Turn(BaseModel):
    event: PossibleEvent
    response: ScoredResponse
    severity: float
    evidence_level: float
    stock_price: float
    public_trust: int

class CrisisState:
    def __init__(self, storyline: Storyline):
        self.dossier: Dict[str, str] = storyline.ground_truth_dossier
        self.initial_state: InitialState = storyline.initial_state

        self.private_fact_ids: Set[str] = set(self.initial_state.private_fact_ids)
        self.public_fact_ids: Set[str] = set(self.initial_state.public_fact_ids)

        self.private_narrative: str = self.initial_state.private_narrative
        self.public_narrative: str = self.initial_state.public_narrative

        # The list of possible events that can happen in this crisis storyline
        self.possible_event_pool: List[PossibleEvent] = storyline.event_pool

        self.turns: List[Turn] = []
        self.turn: int = 1

    def get_public_knowledge_str(self) -> str:
        """
        Assemble the public knowledge into a JSON string
        This will be used as part of the prompt for the PR agent and the Router agent
        """
        facts: Dict[str, str] = {fact_id: self.dossier[fact_id] for fact_id in self.public_fact_ids}
        return json.dumps(facts, indent=4)

    def get_private_knowledge_str(self) -> str:
        """
        Assemble the private knowledge into a JSON string
        This will be used as part of the prompt for the PR agent and the Router agent
        """
        facts: Dict[str, str] = {fact_id: self.dossier[fact_id] for fact_id in self.private_fact_ids}
        return json.dumps(facts, indent=4)

    def apply_event(self, event: PossibleEvent) -> None:
        """
        Apply the effect of an event to the knowledge base in the current state
        The knowledge base of both parties is a crucial factor in the PR agent's decision-making
        """
        # Handle the three types of events w/ if conditions
        # Better do some sanity checks because LLMs can make mistakes sometimes
        if event.type == EventTypeLiteral.INTERNAL_DISCOVERY:
            # A new piece of evidence is discovered through internal investigation
            # Add it to the private knowledge
            if event.target_fact_id not in self.private_fact_ids:
                self.private_fact_ids.add(event.target_fact_id)

        elif event.type == EventTypeLiteral.INFORMATION_LEAK:
            # A piece of information is leaked to the public
            # Remove it from the private knowledge and add it to the public knowledge
            # Ideally, this information is already in the private knowledge
            # because you can't leak something that you don't know about
            if event.target_fact_id in self.private_fact_ids:
                self.private_fact_ids.remove(event.target_fact_id)
            if event.target_fact_id not in self.public_fact_ids:
                self.public_fact_ids.add(event.target_fact_id)

        elif event.type == EventTypeLiteral.EXTERNAL_REACTION:
            # A reaction from the public, such as tweets, news articles, and protests
            # This has no effect on the knowledge base for either party
            pass

    def assemble_storyline_str(self, target: Literal["pr", "adjudicator", "router"]) -> str:
        """
        Assemble the storyline so far into a string
        This will be used as part of the prompt of the PR agent, the Adjudicator agent, and the Router agent
        Args:
            target: Whether this storyline description will be used in the prompt of the PR agent, the Adjudicator agent, or the Router agent
                The language, wording, and information included will be different for the three agents
        Returns:
            The assembled storyline as a string
        """
        subject: str = "Your" if target == "pr" else "The PR Agent's"
        
        storyline: str = ""
        if self.turn == 1:
            # The first day of the crisis
            # Nothing else has happened except the initial event
            if target == "pr":
                # The internal memo is for the PR agent's eyes only
                storyline += f"You received the internal memo: {self.private_narrative}\n"
            else:
                storyline += "The crisis has just happened. No previous turns have occurred."    
            return storyline
        
        else:
            # The breakout (day 1) of the crisis
            storyline += "Day 1:\n"
            storyline += f"BREAKOUT: {self.public_narrative}\n"
            if target == "pr":
                # The internal memo is for the PR agent's eyes only
                storyline += f"You received the internal memo: {self.private_narrative}\n"
            elif target == "router":
                storyline += f"The PR Agent received the internal memo: {self.private_narrative}\n"
                
            storyline += f"{subject} response: {self.turns[0].response.text}\n"
            storyline += f"Crisis Severity: {self.turns[0].severity}/1.0\n"
            storyline += f"Evidence Level: {self.turns[0].evidence_level}/1.0\n"
            storyline += f"Stock Price: ${self.turns[0].stock_price:.2f}\n"
            storyline += f"Public Trust: {self.turns[0].public_trust}/100\n"

            if self.turn >= 3:
                # The subsequent days of the crisis
                for i in range(1, self.turn - 1):
                    turn = self.turns[i]
                    event: PossibleEvent = turn.event
                    storyline += f"\nDAY {i + 1}:\n"

                    if target == "adjudicator":
                        if event.type != EventTypeLiteral.INTERNAL_DISCOVERY:
                            storyline += f"{event.type}: {event.text}\n"
                        else:
                            # The internal discovery event is for the PR agent's eyes only.
                            storyline += "PROGRESS: The company is dealing with the crisis.\n"

                    else:
                        storyline += f"{event.type}: {event.text}\n"

                    storyline += f"{subject} response: {turn.response.text}\n"
                    storyline += f"Crisis Severity: {turn.severity}/1.0\n"
                    storyline += f"Evidence Level: {turn.evidence_level}/1.0\n"
                    storyline += f"Stock Price: ${turn.stock_price:.2f}\n"
                    storyline += f"Public Trust: {turn.public_trust}/100\n"

            return storyline

    def process_agent_reveal(self, agent_response: PRResponse) -> None:
        """
        Update the knowledge base of both parties 
        if the PR agent's response reveals some facts from the private knowledge to the public
        
        Args:
            agent_response: The PR agent's response to the latest event
        """
        revealed_fact_ids = agent_response.revealed_fact_ids
        if isinstance(revealed_fact_ids, list) and revealed_fact_ids != ["N/A"]:
            # The PR agent is instructed to output a list of revealed fact IDs if applicable
            # Ideally, these ids are currently in private knowledge but not in public knowledge
            # Move them from private knowledge to public knowledge
            for fact_id in revealed_fact_ids:
                # Still, some sanity checks wouldn't hurt
                if fact_id not in self.dossier:
                    continue
                if fact_id in self.private_fact_ids:
                    self.private_fact_ids.remove(fact_id)
                if fact_id not in self.public_fact_ids:
                    self.public_fact_ids.add(fact_id)

        elif isinstance(revealed_fact_ids, str):
            # The PR agent is instructed to simply output "N/A" if no facts from the private knowledge are revealed
            # In this case, it won't have any effect on the knowledge base of either party
            pass

    def record_turn(self, turn: Turn) -> None:
        """At the end of each turn of the simulation, call this function to record the turn in the crisis state"""
        self.turns.append(turn)
        self.turn += 1
