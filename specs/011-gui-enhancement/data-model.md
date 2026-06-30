# Data Model: GUI Enhancement

## Session Entity

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | TEXT (UUID) | Primary key |
| `name` | TEXT | User-friendly session name |
| `created_at` | TEXT (ISO8601) | Creation timestamp |
| `updated_at` | TEXT (ISO8601) | Last update timestamp |
| `targets` | JSON | List of target objects |
| `settings` | JSON | GUI settings snapshot |
| `agent_state` | JSON | LangGraph agent state snapshot |
| `status` | TEXT | active/archived |

## Target Entity

| Field | Type | Description |
|-------|------|-------------|
| `target_id` | TEXT (UUID) | Primary key |
| `session_id` | TEXT (UUID) | FK to session |
| `url` | TEXT | Target URL/domain/IP |
| `type` | TEXT | url/domain/ip/cidr |
| `status` | TEXT | pending/running/completed/failed |
| `added_at` | TEXT (ISO8601) | When added |
| `tags` | JSON | User-defined tags |

## Job Entity

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | TEXT (UUID) | Primary key |
| `session_id` | TEXT (UUID) | FK to session |
| `target_id` | TEXT (UUID) | FK to target |
| `type` | TEXT | recon/scan/exploit/full |
| `status` | TEXT | queued/running/completed/failed |
| `agent_state` | JSON | Current LangGraph state |
| `current_node` | TEXT | Active node name |
| `progress_pct` | INTEGER | 0-100 |
| `started_at` | TEXT (ISO8601) | Start timestamp |
| `completed_at` | TEXT (ISO8601) | End timestamp |
| `error` | TEXT | Error message if failed |

## Report Entity

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | TEXT (UUID) | Primary key |
| `session_id` | TEXT (UUID) | FK to session |
| `format` | TEXT | html/md/json |
| `generated_at` | TEXT (ISO8601) | Generation timestamp |
| `file_path` | TEXT | Path to generated file |
| `findings_count` | INTEGER | Number of findings included |

## Relationships

```
Session 1──N Target
Session 1──N Job
Session 1──N Report
Target 1──N Job
Job 1──1 AgentState (embedded JSON)
```

## Blackboard Tables Impact

- New table: `gui_sessions` — session persistence
- New table: `gui_jobs` — job queue tracking
- Existing tables `targets`, `findings`, `entities`, `relations` remain unchanged
- Existing table `global_state` extended with `active_session_id` key
