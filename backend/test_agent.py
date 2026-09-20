"""Smoke-test the configured existing Foundry Agent without changing Azure.

Run manually from ``backend`` with Azure credentials available:
``python test_agent.py``. This makes read/inference calls only; it does not
create or update an agent, version, search connection, index, deployment, or
any other Azure resource.
"""

import json
import sys

from app.services.agent_service import FoundryAgentService


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


QUESTION = "What random seed was used in the experiments?"


def main() -> None:
    result = FoundryAgentService().answer(QUESTION)
    print(f"Question: {QUESTION}")
    print(f"Answer: {result['answer']}")
    print("Citations/source/tool metadata:")
    print(json.dumps(result["sources"], indent=2) if result["sources"] else "None returned by the service.")


if __name__ == "__main__":
    main()
