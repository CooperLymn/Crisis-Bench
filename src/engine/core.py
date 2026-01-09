from typing import Optional, Union, Dict, Any

from .log import CrisisLog, LogEntry
from .state import CrisisState, Turn, ScoredResponse
from .metrics import update_trust_score, update_stock_price

from ..agent.pr import get_pr_response
from ..agent.router import get_next_event
from ..agent.adjudicator import get_adjudicator_score
from ..agent.base import PRResponse, AdjudicatorResponse, RouterResponse
from ..event_factory.constants import Storyline, PossibleEvent, EventTypeLiteral


class PRCrisisSimulation:
    def __init__(self, storyline: Storyline, agent_model: str, pr_completion_kwargs: Optional[Dict[str, Any]] = None):
        self.storyline: Storyline = storyline
        self.state: CrisisState = CrisisState(storyline)
        self.agent_model = agent_model
        self.pr_completion_kwargs = pr_completion_kwargs if pr_completion_kwargs else {}

        self.stock_price: float = 100.0
        self.public_trust: int = 80

        self.crisis_log: CrisisLog = CrisisLog(
            agent_model=agent_model,
            crisis_setup=storyline,
            initial_stock_price=100.0,
            initial_public_trust=80,
            turns=[]
        )

        self.MAX_ITERATION: int = 7

    def run(self) -> CrisisLog:
        """Run the corporate crisis simulation"""
        router_response: Union[RouterResponse, None] = None
        for i in range(self.MAX_ITERATION):
            print(f"Iteration {i + 1} of {self.MAX_ITERATION}")
            if i == 0: 
                # Initialize the first event with the BREAKOUT event
                self.cur_event: PossibleEvent = PossibleEvent(
                    id="",
                    text=self.storyline.initial_state.public_narrative,
                    type=EventTypeLiteral.INFORMATION_LEAK,
                    target_fact_id="",
                    condition=""
                )
            else:
                # Use the Router agent to select the next event
                self.cur_event, router_response = get_next_event(self.state)
                # Apply the event effect to the knowledge base in the current state
                # Such knowledge bases are a crucial factor in the PR agent's decision-making
                self.state.apply_event(self.cur_event)

            print(f"Event: {self.cur_event.text}")

            # Get the response of the PR agent
            pr_response: PRResponse = get_pr_response(
                state=self.state, 
                cur_event=self.cur_event, 
                llm_model=self.agent_model,
                completion_kwargs=self.pr_completion_kwargs
            )
            print(f"Response: {pr_response.public_statement}")
            
            # Get the adjudicator to score the response of the PR agent from the view of the PUBLIC
            # If the event is an internal discovery, pass in a dummy event to avoid information leakage
            if self.cur_event.type == EventTypeLiteral.INTERNAL_DISCOVERY:
                dummy_event: PossibleEvent = PossibleEvent(
                    id="",
                    text="The company is dealing with the crisis.",
                    type=EventTypeLiteral.EXTERNAL_REACTION,
                    target_fact_id="",
                    condition=""
                )
                adjudicator_response: AdjudicatorResponse = get_adjudicator_score(
                    self.state, 
                    dummy_event, 
                    pr_response
                )
            else:
                adjudicator_response: AdjudicatorResponse = get_adjudicator_score(
                    self.state, 
                    self.cur_event, 
                    pr_response
                )
            print(adjudicator_response)

            # Update the stock price and the public trust score
            self._update_metrics(adjudicator_response)

            scored_response: ScoredResponse = ScoredResponse(
                text=pr_response.public_statement,
                accountability=adjudicator_response.accountability,
                transparency=adjudicator_response.transparency,
                empathy=adjudicator_response.empathy,
                costly_signaling=adjudicator_response.costly_signaling
            )

            # Update the crisis storyline state with the new turn
            # This will be used for constructing agents' prompts
            self.state.record_turn(
                Turn(
                    event=self.cur_event,
                    response=scored_response,
                    stock_price=self.stock_price,
                    public_trust=self.public_trust,
                    severity=adjudicator_response.severity,
                    evidence_level=adjudicator_response.evidence_level
                )
            )

            # Record everything that has happened in a log
            # This will be used for result analysis and evaluation
            self.crisis_log.turns.append(
                LogEntry(
                    turn=self.state.turn - 1,
                    router_response=None if i == 0 else router_response,
                    event=self.cur_event,
                    private_fact_ids=list(self.state.private_fact_ids),
                    public_fact_ids=list(self.state.public_fact_ids),
                    response=pr_response,
                    adjudicator_response=adjudicator_response,
                    stock_price=self.stock_price,
                    public_trust=self.public_trust
                )
            )

            # The response of the PR agent may reveal some facts from the private knowledge to the public
            # Update the knowledge base of both parties accordingly
            self.state.process_agent_reveal(pr_response)
        
        return self.crisis_log

    def _update_metrics(self, score: AdjudicatorResponse) -> None:
        """Update the stock price and the public trust score"""
        trust_delta = update_trust_score(score)
        stock_price_delta = update_stock_price(trust_delta, score)

        self.public_trust += trust_delta
        self.public_trust = max(0, min(self.public_trust, 100))

        self.stock_price = self.stock_price * (1 + stock_price_delta / 100.0)

        print(f"Stock Price: {self.stock_price:.2f}, Public Trust: {self.public_trust}/100")

