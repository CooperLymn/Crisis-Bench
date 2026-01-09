import json
from typing import List
from pathlib import Path

from .constants import Storyline, SCENARIO_FACTORY_PROMPT_TEMPLATE
from ..llm.completion import generate_completion, extract_json


def generate_scenario(industry: str) -> Storyline:
    prompt = SCENARIO_FACTORY_PROMPT_TEMPLATE.format(industry=industry)
    for attempt in range(3):
        try:
            response = generate_completion(
                prompt=prompt,
                model="claude-sonnet-4-5-20250929",
                temperature=1.0
            )
            content: str = response.choices[0].message.content
            content = extract_json(content)
            scenario = Storyline.model_validate_json(content)
            return scenario

        except Exception as e:
            print(e)
            continue

def main():
    with open("src/event_factory/seeds.md", "r") as f:
        seeds = f.readlines()

    signature: str = "Finance: "
    industries: List[str] = []

    for line in seeds:
        if signature in line:
            industry = line[line.find(signature):]
            industries.append(industry.strip())

    for idx, industry in enumerate(industries):
        response = generate_scenario(industry=industry)

        save_path: Path = Path(f"data/scenarios/finance/finance_{idx}.json")

        with open(save_path, "w") as f:
            json.dump(response.model_dump(), f, indent=4)
            print(f"Scenario saved to {save_path}")


if __name__ == "__main__":
    main()

