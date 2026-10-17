# 🗣️ neuraldeep-whisper-1

Speech-to-text through the NeuralDeep Hub `whisper-1` model
(OpenAI-compatible `POST /v1/audio/transcriptions`).
Transcription is blocked until a remaining-quota endpoint for whisper-1 is
verified; the helper runs only a read-only Starter preflight today.

A [Coddy](https://coddy.dev) / AI-agent skill for the **NeuralDeep Hub API**.
Model page: <https://hub.neuraldeep.ru/models/whisper-1>.

## Author

This skill was authored by **Claude Opus 5.5** after the neuraldeep-* skills
authored by the **kimi2.6** and **qwen3.8 27b** models, and is published by **viktor-drobek**.

## Install

```bash
# via the skillsbd catalog
npx skillsbd add viktor-drobek/neuraldeep-whisper-1/neuraldeep-whisper-1

# or directly from this repo
npx skillsbd add https://github.com/viktor-drobek/neuraldeep-whisper-1 --skill neuraldeep-whisper-1
```

## Requirements

- A NeuralDeep API key (`sk-...`). The skill reads it from
  `${CODDY_HOME:-~/.coddy}/providers/neuraldeep/neuraldeep-auth.json` (field `api_key`),
  falling back to `NEURALDEEP_API_KEY` when the file/key is missing, null, empty, or malformed.
- Python 3.10+ (standard library only).
- Get a key at <https://neuraldeep.ru> (Hub) or via `coddy providers login neuraldeep`.

## Usage

See [`SKILL.md`](./SKILL.md) for the endpoint reference, the preflight command,
and the cost and safety rules.

## Starter guard and Relay handoff

See [STARTER_RELAY.md](./STARTER_RELAY.md) for the guard, private state, and the
optional artifact-based Relay envelope. The helper checks live service quota
rather than hard-coding daily limits. whisper-1 has no verified remaining-quota
endpoint, so transcription is blocked. The call is synchronous, so nothing can be resumed.

Run offline tests: `python3 -B -m unittest discover -s tests`.

## License

[MIT](./LICENSE)
