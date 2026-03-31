"""
ResolveX MCP tools package.

This package contains internal operational tools used by the multi-agent system:
- task management
- notes / audit trail
- calendar / deadline tracking
"""

from .task_tool import (
    create_task,
    update_task_status,
    add_task_note,
    get_task,
    get_tasks,
    get_open_task_summary,
)

from .notes_tool import (
    create_note,
    append_note,
    update_note,
    get_note,
    get_notes_by_entity,
    get_recent_notes,
    get_notes_summary,
)

from .calendar_tool import (
    create_event,
    complete_event,
    reschedule_event,
    get_event,
    get_upcoming_events,
    get_overdue_events,
    get_events_by_entity,
    get_calendar_summary,
)

__all__ = [
    # task tool
    "create_task",
    "update_task_status",
    "add_task_note",
    "get_task",
    "get_tasks",
    "get_open_task_summary",

    # notes tool
    "create_note",
    "append_note",
    "update_note",
    "get_note",
    "get_notes_by_entity",
    "get_recent_notes",
    "get_notes_summary",

    # calendar tool
    "create_event",
    "complete_event",
    "reschedule_event",
    "get_event",
    "get_upcoming_events",
    "get_overdue_events",
    "get_events_by_entity",
    "get_calendar_summary",
]