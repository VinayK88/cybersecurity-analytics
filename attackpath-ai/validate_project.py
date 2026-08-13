"""Validate project artifacts without third-party dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from attackpath_ai.cli import self_test  # noqa: E402


def main() -> None:
    notebook_path = PROJECT_ROOT / "notebooks" / "01_identity_agent_attack_detection.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 14
    markdown = "\n".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "markdown")
    for heading in ("## tl;dr", "## Context & Methods", "## Data", "## Results", "## Takeaways", "## Checks", "## Next Steps"):
        assert heading in markdown, f"missing required notebook section: {heading}"
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell["execution_count"] is not None for cell in code_cells)
    assert not any(output["output_type"] == "error" for cell in code_cells for output in cell["outputs"])
    figures = sum("image/svg+xml" in output.get("data", {}) for cell in code_cells for output in cell["outputs"])
    assert figures >= 3
    assert (PROJECT_ROOT / "assets" / "dashboard-preview.svg").read_text(encoding="utf-8").startswith("<svg")
    assert (PROJECT_ROOT / "data" / "synthetic_events.csv").stat().st_size > 50_000
    evaluation = json.loads((PROJECT_ROOT / "artifacts" / "evaluation.json").read_text(encoding="utf-8"))
    assert evaluation["metadata"]["safety"].startswith("simulation only")
    gates = self_test()
    print(json.dumps({"status": "PASS", "notebook_code_cells": len(code_cells), "figures": figures, **gates}, indent=2))


if __name__ == "__main__":
    main()
