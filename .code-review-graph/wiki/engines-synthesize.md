# engines-synthesize

## Overview

Directory-based community: src/engines

- **Size**: 19 nodes
- **Cohesion**: 0.3032
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| concat_mp3_chunks | Function | /Users/johnny/projects/tts-new/03-development/src/engines/synthesis.py | 38-44 |
| synthesize_one | Function | /Users/johnny/projects/tts-new/03-development/src/engines/synthesis.py | 47-71 |
| synthesize_chunks | Function | /Users/johnny/projects/tts-new/03-development/src/engines/synthesis.py | 74-112 |
| synthesize_text | Function | /Users/johnny/projects/tts-new/03-development/src/engines/synthesis.py | 115-130 |
| apply_lexicon | Function | /Users/johnny/projects/tts-new/03-development/src/engines/taiwan_linguistic.py | 112-124 |
| _force_split | Function | /Users/johnny/projects/tts-new/03-development/src/engines/text_splitter.py | 35-37 |
| _simple_split | Function | /Users/johnny/projects/tts-new/03-development/src/engines/text_splitter.py | 40-42 |
| _apply_boundary_tier | Function | /Users/johnny/projects/tts-new/03-development/src/engines/text_splitter.py | 45-55 |
| split_text | Function | /Users/johnny/projects/tts-new/03-development/src/engines/text_splitter.py | 58-96 |
| Segment | Class | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 70-79 |
| ParsedSSML | Class | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 83-94 |
| _parse_break_time | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 97-109 |
| _digits_to_chinese | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 112-119 |
| _cardinal_to_chinese | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 122-167 |
| under_100 | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 145-152 |
| _local_tag | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 170-175 |
| _emit | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 178-284 |
| _fallback_plain | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 287-306 |
| parse_ssml | Function | /Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py | 309-365 |

## Execution Flows

- **post_speech** (criticality: 0.72, depth: 6)

## Dependencies

### Outgoing

- `append` (31 edge(s))
- `join` (5 edge(s))
- `warning` (5 edge(s))
- `int` (4 edge(s))
- `get` (4 edge(s))
- `len` (4 edge(s))
- `split` (3 edge(s))
- `group` (3 edge(s))
- `str` (2 edge(s))
- `float` (2 edge(s))
- `itertext` (2 edge(s))
- `isinstance` (2 edge(s))
- `extend` (2 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_mutation_kills.py::test_mutation_kill_boundary_tier` (2 edge(s))
- `strip` (1 edge(s))

### Incoming

- `/Users/johnny/projects/tts-new/03-development/src/engines/ssml_parser.py` (10 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/engines/synthesis.py` (4 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/engines/text_splitter.py` (4 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_mutation_kills.py::test_mutation_kill_boundary_tier` (2 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/speech_router.py::_synthesize` (1 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/engines/taiwan_linguistic.py` (1 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_mutation_kills_extra.py::test_mutation_kill_text_splitter_hard_cap_boundary` (1 edge(s))
