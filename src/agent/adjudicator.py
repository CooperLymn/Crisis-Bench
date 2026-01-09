from .base import AdjudicatorResponse, PRResponse
from .constants import ADJUDICATOR_PROMPT_TEMPLATE
from ..engine.state import CrisisState
from ..event_factory.constants import PossibleEvent
from ..llm.completion import generate_completion, extract_json


def get_adjudicator_score(state: CrisisState, cur_event: PossibleEvent, agent_response: PRResponse) -> AdjudicatorResponse:
    """
    Get the Adjudicator Agent to score the PR agent's response to the latest event from the view of the PUBLIC
    The Adjudicator will base its score on:
        - The crisis storyline so far (every event and every response)
        - The latest event the agent must respond to
        - The PR agent's response to the latest event

    Args:
        state: The current state of the crisis
        cur_event: The latest event
        agent_response: The PR agent's response to the latest event

    Returns:
        The Adjudicator's score of the PR agent's response
    """
    storyline: str = state.assemble_storyline_str(target="adjudicator")
    event_str: str = cur_event.text
    prompt = ADJUDICATOR_PROMPT_TEMPLATE.format(
        storyline=storyline, 
        latest_event=event_str, 
        statement=agent_response.public_statement
    )
    
    for attempt in range(3):
        try:
            response = generate_completion(
                prompt=prompt,
                model="gpt-5-mini",
                temperature=0,
                extra_body={"reasoning_effort": "low"},
            )
            content = response.choices[0].message.content
            content = extract_json(content)
            scores = AdjudicatorResponse.model_validate_json(content)
            return scores

        except Exception as e:
            print(f"Error while scoring the agent's response: {e}")
            continue

    raise Exception(f"Failed to score the PR agent's response after {attempt} attempts")
    