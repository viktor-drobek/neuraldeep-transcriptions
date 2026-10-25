# 🗣️ neuraldeep-transcriptions

Speech-to-text on the NeuralDeep Hub with `gigaam-v3` (default), `whisper-1` and
`whisper-podlodka-turbo` (OpenAI-compatible `POST /v1/audio/transcriptions`). The
helper transcribes with a wallet key after the user approves the estimated cost;
a subscription key stays blocked until a remaining-quota endpoint is verified.

A [Coddy](https://coddy.dev) / AI-agent skill for the **NeuralDeep Hub API**.
Model pages: <https://hub.neuraldeep.ru/models/gigaam-v3>, <https://hub.neuraldeep.ru/models/whisper-1>,
<https://hub.neuraldeep.ru/models/whisper-podlodka-turbo>.

## Author

**Viktor Drobek**

## Install

```bash
# via the skillsbd catalog
npx skillsbd add viktor-drobek/neuraldeep-transcriptions/neuraldeep-transcriptions

# or directly from this repo
npx skillsbd add https://github.com/viktor-drobek/neuraldeep-transcriptions --skill neuraldeep-transcriptions
```

## Requirements

- A NeuralDeep API key (`sk-...`) in this skill's own variable `NEURALDEEP_TRANSCRIPTIONS_API_KEY` (several
  keys may be separated by commas), or the shared `NEURALDEEP_API_KEY`, set in the
  environment or in `${CODDY_HOME:-~/.coddy}/.env`:

  ```bash
  echo 'NEURALDEEP_TRANSCRIPTIONS_API_KEY=sk-...' >> ~/.coddy/.env
  ```
- Python 3.10+ (standard library only).
- Get a key at <https://neuraldeep.ru> (Hub).

## Usage

See [`SKILL.md`](./SKILL.md) for the endpoint reference, the preflight command,
and the cost and safety rules.

## Starter guard and Relay handoff

See [STARTER_RELAY.md](./STARTER_RELAY.md) for the guard, private state, and the
optional artifact-based Relay envelope. The helper checks live service quota
rather than hard-coding daily limits. Transcription has no verified remaining-quota
endpoint, so a subscription key is blocked; a wallet key pays only up to the amount
the user approved (`--wallet-limit`). The call is synchronous, so nothing can be resumed.

Run offline tests: `python3 -B -m unittest discover -s tests`.

## License

[MIT](./LICENSE)
