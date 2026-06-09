# api-synthesize

## Overview

Directory-based community: src/api

- **Size**: 13 nodes
- **Cohesion**: 0.3077
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| _parse_args | Function | /Users/johnny/projects/tts-new/03-development/src/api/cli.py | 31-59 |
| _synthesize_text | Function | /Users/johnny/projects/tts-new/03-development/src/api/cli.py | 62-80 |
| main | Function | /Users/johnny/projects/tts-new/03-development/src/api/cli.py | 83-146 |
| lifespan | Function | /Users/johnny/projects/tts-new/03-development/src/api/main.py | 44-57 |
| create_app | Function | /Users/johnny/projects/tts-new/03-development/src/api/main.py | 60-84 |
| global_exception_handler | Function | /Users/johnny/projects/tts-new/03-development/src/api/main.py | 77-82 |
| post_speech | Function | /Users/johnny/projects/tts-new/03-development/src/api/speech_router.py | 39-76 |
| _synthesize | Function | /Users/johnny/projects/tts-new/03-development/src/api/speech_router.py | 50-55 |
| sanitize_log_extra | Function | /Users/johnny/projects/tts-new/03-development/src/api/utils.py | 21-35 |
| build_error_response | Function | /Users/johnny/projects/tts-new/03-development/src/api/utils.py | 38-47 |
| log_cli_event | Function | /Users/johnny/projects/tts-new/03-development/src/api/cli_logging.py | 16-18 |
| format_cli_error | Function | /Users/johnny/projects/tts-new/03-development/src/api/cli_logging.py | 21-25 |
| validate_backend_url | Function | /Users/johnny/projects/tts-new/03-development/src/api/cli_logging.py | 28-35 |

## Execution Flows

- **post_speech** (criticality: 0.72, depth: 6)
- **main** (criticality: 0.57, depth: 1)
- **lifespan** (criticality: 0.52, depth: 1)
- **create_app** (criticality: 0.52, depth: 1)
- **global_exception_handler** (criticality: 0.52, depth: 1)

## Dependencies

### Outgoing

- `add_argument` (8 edge(s))
- `str` (7 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr07.py::test_fr_07_cli` (6 edge(s))
- `info` (5 edge(s))
- `warning` (5 edge(s))
- `open` (3 edge(s))
- `HTTPException` (3 edge(s))
- `run` (2 edge(s))
- `write` (2 edge(s))
- `include_router` (2 edge(s))
- `ArgumentParser` (1 edge(s))
- `parse_args` (1 edge(s))
- `AsyncClient` (1 edge(s))
- `post` (1 edge(s))
- `raise_for_status` (1 edge(s))

### Incoming

- `/Users/johnny/projects/tts-new/03-development/tests/test_fr07.py::test_fr_07_cli` (6 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/main.py` (4 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/cli.py` (3 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/cli_logging.py` (3 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/speech_router.py` (2 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/utils.py` (2 edge(s))
