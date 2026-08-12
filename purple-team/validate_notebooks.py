from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = ROOT / "notebooks"
EXPECTED_NOTEBOOKS = 5
REQUIRED_SECTIONS = (
    "## Goal",
    "## Setup",
    "## Steps",
    "## Visual Insights & ML Extension",
    "## Checks",
    "## Next Steps",
)


def source_text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def validate_structure(path: Path, payload: dict) -> None:
    if payload.get("nbformat") != 4:
        raise ValueError(f"{path.name}: expected nbformat 4")
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path.name}: notebook has no cells")

    markdown_text = "\n".join(
        source_text(cell) for cell in cells if cell.get("cell_type") == "markdown"
    )
    missing = [section for section in REQUIRED_SECTIONS if section not in markdown_text]
    if missing:
        raise ValueError(f"{path.name}: missing sections {missing}")
    if "Safety boundary" not in markdown_text:
        raise ValueError(f"{path.name}: missing explicit safety boundary")

    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    if len(code_cells) != 5:
        raise ValueError(f"{path.name}: expected exactly five code cells")


def capture_figures(cell: dict) -> int:
    import matplotlib.pyplot as plt

    figure_count = 0
    for figure_number in list(plt.get_fignums()):
        figure = plt.figure(figure_number)
        image_buffer = io.BytesIO()
        figure.savefig(
            image_buffer,
            format="png",
            dpi=115,
            bbox_inches="tight",
            facecolor="white",
        )
        cell["outputs"].append(
            {
                "data": {
                    "image/png": base64.b64encode(image_buffer.getvalue()).decode("ascii"),
                    "text/plain": [f"<Figure {figure_number}: embedded validation render>"],
                },
                "metadata": {},
                "output_type": "display_data",
            }
        )
        figure_count += 1
    plt.close("all")
    return figure_count


def execute_notebook(path: Path) -> tuple[int, int, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_structure(path, payload)
    namespace = {"__name__": "__main__"}
    execution_count = 0
    output_characters = 0
    rendered_figures = 0

    for cell_index, cell in enumerate(payload["cells"], start=1):
        if cell.get("cell_type") != "code":
            continue

        execution_count += 1
        cell["execution_count"] = execution_count
        cell["outputs"] = []
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()

        try:
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                exec(compile(source_text(cell), f"{path.name}:cell-{cell_index}", "exec"), namespace)
        except Exception as exc:
            captured = output_buffer.getvalue() + error_buffer.getvalue()
            if captured:
                cell["outputs"].append(
                    {"name": "stdout", "output_type": "stream", "text": captured.splitlines(keepends=True)}
                )
            cell["outputs"].append(
                {
                    "ename": type(exc).__name__,
                    "evalue": str(exc),
                    "output_type": "error",
                    "traceback": traceback.format_exc().splitlines(),
                }
            )
            path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            raise RuntimeError(f"{path.name}: execution failed in code cell {cell_index}") from exc

        captured = output_buffer.getvalue() + error_buffer.getvalue()
        output_characters += len(captured)
        if captured:
            cell["outputs"].append(
                {"name": "stdout", "output_type": "stream", "text": captured.splitlines(keepends=True)}
            )
        rendered_figures += capture_figures(cell)

    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return execution_count, output_characters, rendered_figures


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))
    notebook_paths = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    if len(notebook_paths) != EXPECTED_NOTEBOOKS:
        raise ValueError(f"Expected {EXPECTED_NOTEBOOKS} notebooks, found {len(notebook_paths)}")

    total_cells = 0
    total_figures = 0
    for notebook_path in notebook_paths:
        code_cells, output_characters, rendered_figures = execute_notebook(notebook_path)
        total_cells += code_cells
        total_figures += rendered_figures
        print(
            f"validated {notebook_path.name}: {code_cells} code cells, "
            f"{rendered_figures} figures, {output_characters} output characters"
        )

    print(
        f"validated {len(notebook_paths)} notebooks, {total_cells} code cells, "
        f"and {total_figures} embedded figures"
    )


if __name__ == "__main__":
    main()
