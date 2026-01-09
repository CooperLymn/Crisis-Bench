import json
from typing import Union, Tuple

from .base import RouterResponse
from .constants import ROUTER_AGENT_PROMPT_TEMPLATE, ROUTER_AGENT_SYSTEM_PROMPT
from ..engine.state import CrisisState, Turn
from ..event_factory.constants import PossibleEvent
from ..llm.completion import generate_completion, extract_json


def get_next_event(state: CrisisState) -> Tuple[PossibleEvent, RouterResponse]:
    """
    Get the Router Agent to select the mostly likely next event to happen in the next turn of the simulation
    The Router will base its decision on:
        - The current public knowledge base
        - The current private knowledge base
        - The latest event
        - The PR agent's response to the latest event
        - An event pool of all possible events in this storyline

    Args:
        state: The current state of the crisis

    Returns:
        The next event to happen
    """
    storyline: str = state.assemble_storyline_str(target="router")
    event_pool_str: str = json.dumps([event.model_dump() for event in state.possible_event_pool], indent=4)

    latest: Turn = state.turns[-1]

    user_prompt = ROUTER_AGENT_PROMPT_TEMPLATE.format(
        storyline=storyline,
        public_knowledge=state.get_public_knowledge_str(),
        private_knowledge=state.get_private_knowledge_str(),
        latest_event=latest.event.text,
        statement=latest.response.text,
        event_pool=event_pool_str
    )

    for attempt in range(3):
        try:
            response = generate_completion(
                prompt=user_prompt,
                model="gpt-5-mini",
                temperature=0,
                system_prompt=ROUTER_AGENT_SYSTEM_PROMPT,
                extra_body={"reasoning_effort": "low"},
            )
            content = response.choices[0].message.content
            content = extract_json(content)
            response = RouterResponse.model_validate_json(content)

            next_event: Union[PossibleEvent, None] = None
            for event in state.possible_event_pool:
                if event.id == response.selected_event_id:
                    next_event = event
                    # remove the selected event from the pool
                    state.possible_event_pool.remove(event)
                    break

            if next_event is not None:
                return next_event, response

            raise ValueError(f"No event found for event id: {response.selected_event_id}")

        except Exception as e:
            print(e)
            continue