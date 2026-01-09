import os
import json
import argparse
from pathlib import Path

from src.llm.config import LLMModelLiterals
from src.engine.core import PRCrisisSimulation, CrisisLog
from src.event_factory.constants import Storyline, CrisisCategoryLiteral


def main():
    parser = argparse.ArgumentParser(description="Run PR crisis simulation")
    parser.add_argument(
        "--crisis_category",
        type=str,
        required=True,
        help=f"Crisis category. Options: {', '.join([getattr(CrisisCategoryLiteral, attr) for attr in dir(CrisisCategoryLiteral) if not attr.startswith('_')])}"
    )
    parser.add_argument(
        "--agent_model",
        type=str,
        required=True,
        help=f"Agent model. Options: {', '.join([getattr(LLMModelLiterals, attr) for attr in dir(LLMModelLiterals) if not attr.startswith('_')])}"
    )
    args = parser.parse_args()
    
    crisis_category: str = args.crisis_category
    agent_model: str = args.agent_model

    storyline_folder: Path = Path(f"data/scenarios/{crisis_category}")

    result_folder: Path = Path(f"data/trajectory/{agent_model}/{crisis_category}")
    if not result_folder.exists():
        result_folder.mkdir(parents=True, exist_ok=True)

    print(f"Running simulations for {agent_model} in {crisis_category}\n")

    for root, dirs, files in os.walk(storyline_folder):
        files.sort()
        for file in files:
            print("-" * 90)
            print(f"Running simulation for {file}")
            # Load crisis storyline
            storyline_path: Path = Path(root) / file
            storyline = Storyline.model_validate_json(storyline_path.read_text())
              
            # Run simulation
            simulation: PRCrisisSimulation = PRCrisisSimulation(
                storyline=storyline, 
                agent_model=agent_model,
                pr_completion_kwargs={"extra_body": {"reasoning_effort": "high"}}
                # pr_completion_kwargs={"extra_body": {"response_format": {"type": "json_object"}}}
            )
            log: CrisisLog = simulation.run()

            # Save the trajectory   
            with open(result_folder / file, "w") as f:
                json.dump(log.model_dump(), f, indent=4)
            print(f"Trajectory saved to {result_folder / file}")


if __name__ == "__main__":
    main()