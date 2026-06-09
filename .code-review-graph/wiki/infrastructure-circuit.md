# infrastructure-circuit

## Overview

Directory-based community: src/infrastructure

- **Size**: 27 nodes
- **Cohesion**: 0.3037
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| ConversionError | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py | 28-34 |
| FFmpegUnavailableError | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py | 37-52 |
| __init__ | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py | 46-52 |
| _run_ffmpeg | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py | 55-100 |
| convert_mp3_to_wav | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py | 103-118 |
| convert_wav_to_mp3 | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py | 121-137 |
| CircuitOpenError | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 30-35 |
| CircuitBreaker | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 38-156 |
| __init__ | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 47-61 |
| _transition | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 63-89 |
| call | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 91-121 |
| _on_success | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 123-132 |
| _on_failure | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 134-148 |
| reset | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py | 150-156 |
| validate_config | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/config.py | 68-81 |
| get_config_snapshot | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/config.py | 84-97 |
| get_circuit_state | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/health.py | 35-46 |
| post_circuit_reset | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/health.py | 50-58 |
| SpeechRequest | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/models.py | 35-55 |
| input_not_blank | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/models.py | 49-55 |
| SpeechResponse | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/models.py | 58-66 |
| make_cache_key | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py | 33-49 |
| RedisCache | Class | /Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py | 52-112 |
| __init__ | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py | 67-71 |
| is_available | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py | 73-77 |
| get | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py | 79-95 |
| set | Function | /Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py | 97-112 |

## Execution Flows

- **input_not_blank** (criticality: 0.60, depth: 1)
- **__init__** (criticality: 0.52, depth: 1)
- **get_circuit_state** (criticality: 0.52, depth: 1)
- **post_circuit_reset** (criticality: 0.52, depth: 1)
- **__init__** (criticality: 0.52, depth: 1)
- **reset** (criticality: 0.50, depth: 1)
- **set** (criticality: 0.50, depth: 1)
- **call** (criticality: 0.47, depth: 1)

## Dependencies

### Outgoing

- `/Users/johnny/projects/tts-new/03-development/tests/test_fr08.py::test_fr_08_audio_converter` (21 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr06.py::test_fr_06_redis_cache` (12 edge(s))
- `append` (5 edge(s))
- `str` (4 edge(s))
- `time_func` (3 edge(s))
- `Exception` (2 edge(s))
- `mkstemp` (2 edge(s))
- `close` (2 edge(s))
- `unlink` (2 edge(s))
- `BaseModel` (2 edge(s))
- `info` (2 edge(s))
- `ConversionError` (1 edge(s))
- `RuntimeError` (1 edge(s))
- `super` (1 edge(s))
- `which` (1 edge(s))

### Incoming

- `/Users/johnny/projects/tts-new/03-development/tests/test_fr08.py::test_fr_08_audio_converter` (30 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr06.py::test_fr_06_redis_cache` (12 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/audio_converter.py` (8 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/health.py` (5 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/circuit_breaker.py` (4 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/models.py` (4 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/redis_cache.py` (4 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/infrastructure/config.py` (2 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr08.py::_mp3_to_wav_task` (1 edge(s))
- `/Users/johnny/projects/tts-new/03-development/tests/test_fr08.py::_wav_to_mp3_task` (1 edge(s))
- `/Users/johnny/projects/tts-new/03-development/src/api/speech_router.py` (1 edge(s))
