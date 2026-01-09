import time
from typing import Union, Dict, Any, Optional

from .base import PRResponse
from .constants import PR_AGENT_PROMPT_TEMPLATE, PR_AGENT_SYSTEM_PROMPT
from ..engine.state import CrisisState, Turn
from ..llm.completion import generate_completion, extract_json
from ..event_factory.constants import PossibleEvent, EventTypeLiteral


def get_pr_response(
    state: CrisisState, 
    cur_event: PossibleEvent, 
    llm_model: str, 
    completion_kwargs: Optional[Dict[str, Any]] = None
) -> PRResponse:
    """
    Get the PR Agent to respond to the latest event
    The PR Agent will base its response on:
        - The crisis storyline so far (every event and every response)
        - The current public knowledge base
        - The current private knowledge base
        - The latest event the agent must respond to

    Args:
        state: The current state of the crisis
        cur_event: The latest event
        llm_model: The LLM model to use for the PR agent

    Returns:
        The PR agent's response to the latest event
    """
    storyline: str = state.assemble_storyline_str(target="pr")
    event_str: str = cur_event.text

    completion_kwargs_ = completion_kwargs if completion_kwargs else {}

    if cur_event.type == EventTypeLiteral.INTERNAL_DISCOVERY:
        event_str += "This is an internal event and the public is currently not aware of it."

    latest: Union[Turn, None] = state.turns[-1] if state.turns else None

    prompt = PR_AGENT_PROMPT_TEMPLATE.format(
        turn_number=state.turn,
        current_stock=latest.stock_price if latest else 100.0,
        current_trust=latest.public_trust if latest else 80,
        storyline=storyline,
        public_knowledge=state.get_public_knowledge_str(),
        private_knowledge=state.get_private_knowledge_str(),
        latest_event=event_str,
    )

    # Do some retries for robustness because LLMs can make mistakes sometimes
    for attempt in range(3):
        try:
            response = generate_completion(
                prompt=prompt,
                model=llm_model,
                temperature=0,
                system_prompt=PR_AGENT_SYSTEM_PROMPT,
                **completion_kwargs_
            )
            content = response.choices[0].message.content
            content = extract_json(content)

            # Sometimes the LLM will return the content in a weird format, so we need to clean it up
            # content = content.replace("{{", "{")
            # content = content.replace("}}", "}")
            # content = content.replace("```\n{", "{")
            # content = content.replace("}\n```", "}")
            return PRResponse.model_validate_json(content)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
            continue

    raise Exception(f"Failed to generate a PR response after {attempt + 1} attempts")