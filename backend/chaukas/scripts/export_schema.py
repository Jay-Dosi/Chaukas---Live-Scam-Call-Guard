"""Export JSON Schema for wire protocol — PRD §5.

Generates packages/protocol/schema.json from pydantic models.
"""

import json
from pathlib import Path

from chaukas.ws.protocol import (
    ClientMessage,
    ServerEvent,
)
from chaukas.models.base import Analysis, Segment, SignalHit, LlmAssessment


def main():
    # Collect all models
    models = {
        "ClientMessage": ClientMessage,
        "ServerEvent": ServerEvent,
        "Segment": Segment,
        "Analysis": Analysis,
        "SignalHit": SignalHit,
        "LlmAssessment": LlmAssessment,
    }

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Chaukas Protocol",
        "definitions": {},
    }

    defs = {}
    for name, model in models.items():
        defs[name] = model.model_json_schema()

    schema["definitions"] = defs
    schema["$ref"] = "#/definitions/ClientMessage"

    # Write
    out_dir = Path(__file__).parent.parent.parent.parent / "packages" / "protocol"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "schema.json"

    with open(out_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"Schema written to {out_path}")


if __name__ == "__main__":
    main()