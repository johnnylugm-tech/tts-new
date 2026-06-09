# tests-lexicon

## Overview

Directory-based community: tests

- **Size**: 92 nodes
- **Cohesion**: 0.0893
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| test_redis_cache_get_returns_none_when_unavailable | Test | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 25-27 |
| test_redis_cache_set_noop_when_unavailable | Test | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 30-33 |
| test_redis_cache_set_exception_marks_unavailable | Test | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 36-47 |
| _FailingClient | Class | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 37-42 |
| get | Function | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 38-39 |
| setex | Function | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 41-42 |
| test_synthesize_chunks_raises_on_empty | Test | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 52-54 |
| test_cli_main_no_text_no_file_returns_0 | Test | /Users/johnny/projects/tts-new/03-development/tests/test_coverage_gaps.py | 59-62 |
| test_fr_01_lexicon_coverage | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 64-151 |
| test_apply_lexicon_empty_string | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 160-164 |
| test_apply_lexicon_no_match | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 167-172 |
| test_apply_lexicon_punctuation_only | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 175-180 |
| test_apply_lexicon_multiple_matches | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 183-188 |
| test_apply_lexicon_longest_match_first | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 191-203 |
| test_apply_lexicon_preserves_position | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 206-213 |
| test_apply_lexicon_bopomofo_output | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 216-226 |
| test_apply_lexicon_large_input | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 229-237 |
| test_lexicon_all_entries_are_strings | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 240-246 |
| test_apply_lexicon_idempotent | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 249-257 |
| test_lexicon_min_size_constant | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 260-265 |
| test_apply_lexicon_overlapping_tokens | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr01.py | 269-281 |
| test_fr_02_ssml_tags | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr02.py | 102-395 |
| test_fr_02_coverage_supplement | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr02.py | 398-504 |
| _ssml | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr02.py | 408-409 |
| test_fr_03_text_splitter | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr03.py | 126-262 |
| test_fr_03_text_splitter_edge_cases | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr03.py | 315-426 |
| _MockClock | Class | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 116-130 |
| __init__ | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 123-124 |
| __call__ | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 126-127 |
| advance | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 129-130 |
| _ok | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 134-136 |
| _fail | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 139-141 |
| test_fr_05_circuit_breaker | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 158-199 |
| _run_breaker_case | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 206-418 |
| _tracked_fail | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 282-285 |
| _run_router_case | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr05.py | 425-489 |
| _expected_key | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr06.py | 57-61 |
| test_fr_06_redis_cache | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr06.py | 80-232 |
| _make_mock_post | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr07.py | 54-60 |
| test_fr_07_cli | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr07.py | 64-198 |
| _make_wav | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 44-55 |
| _ffmpeg_side_effect | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 79-92 |
| _run | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 87-91 |
| test_fr_08_audio_converter | Test | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 125-402 |
| _capturing_run | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 144-149 |
| _capturing_run2 | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 164-169 |
| _mp3_to_wav_task | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 255-260 |
| _wav_to_mp3_task | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 262-266 |
| _failing_run | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 333-334 |
| _bad_exit_run | Function | /Users/johnny/projects/tts-new/03-development/tests/test_fr08.py | 373-374 |

*... and 42 more members.*

## Execution Flows

No execution flows pass through this community.

## Dependencies

### Outgoing

- `len` (78 edge(s))
- `patch` (65 edge(s))
- `AsyncMock` (39 edge(s))
- `isinstance` (30 edge(s))
- `parse_ssml` (27 edge(s))
- `get` (25 edge(s))
- `raises` (23 edge(s))
- `apply_lexicon` (22 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py::convert_mp3_to_wav` (16 edge(s))
- `call` (15 edge(s))
- `_cardinal_to_chinese` (14 edge(s))
- `range` (11 edge(s))
- `fail` (10 edge(s))
- `str` (9 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py::convert_wav_to_mp3` (9 edge(s))

### Incoming

- `len` (75 edge(s))
- `patch` (60 edge(s))
- `isinstance` (27 edge(s))
- `parse_ssml` (27 edge(s))
- `apply_lexicon` (22 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr08.py` (15 edge(s))
- `AsyncMock` (15 edge(s))
- `get` (14 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py::convert_mp3_to_wav` (14 edge(s))
- `_cardinal_to_chinese` (14 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr01.py` (13 edge(s))
- `raises` (12 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_main_and_models.py` (11 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_mutation_kills_extra.py` (10 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_router_speech.py` (10 edge(s))
