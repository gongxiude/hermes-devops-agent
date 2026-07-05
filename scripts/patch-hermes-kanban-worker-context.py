from __future__ import annotations

from pathlib import Path


TARGET = Path("/opt/hermes/hermes_cli/kanban_db.py")

OLD = '    prompt = f"work kanban task {task.id}"\n'

NEW = '''    try:
        with connect(board=board) as _worker_context_conn:
            worker_context = build_worker_context(_worker_context_conn, task.id)
    except Exception as exc:
        worker_context = (
            f"# Kanban task {task.id}\\n\\n"
            f"Context lookup failed before worker spawn: {exc!r}\\n"
            "Call kanban_show once, then execute or block the task."
        )

    prompt = (
        f"You are the Hermes Kanban worker for task {task.id}.\\n\\n"
        "Execute the task now. Do not watch, wait, or poll the task status.\\n"
        "The full task context is below, so do not call kanban_show unless the context is missing or unreadable.\\n"
        "If you call kanban_show, call it at most once, then perform the work.\\n"
        "Finish with exactly one terminal Kanban action: kanban_complete for success or kanban_block for a blocker.\\n\\n"
        f"{worker_context}"
    )
'''


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if NEW in text:
        print("kanban worker context patch already applied")
        return 0
    if OLD not in text:
        raise SystemExit("expected kanban worker prompt line not found")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("kanban worker context patch applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
