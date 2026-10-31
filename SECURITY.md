# Security policy

SkyQueue is a hackathon prototype. It is not an operational air traffic tool, and no plan it produces should be used to move real aircraft.

## Supported version

Only the `main` branch is supported. Fixes go there; there are no release branches.

## Reporting a problem

Please report security issues privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. That opens a private advisory that only the maintainers can see.

Please don't open a public issue for a security problem. Include what you found, how to reproduce it, and what it affects (for example, the live site, a key, or the audit log). We will reply on the advisory.

## How API keys are handled

- **Server key.** Live runs from the server or the command line read `ANTHROPIC_API_KEY` (and optionally `ANTHROPIC_WORKSPACE_ID`) from `.env`. `.env` is listed in `.gitignore` and must never be committed. Copy `.env.example` instead.
- **Visitor keys.** On the live site a visitor can paste a Claude or OpenRouter key. It is held in that browser's Streamlit session only, used for that visitor's live run, and sent only to the provider it belongs to (Anthropic, or OpenRouter for keys starting `sk-or-`). It is not written to disk, the SQLite log or the cache.
- **Cache.** Model replies are cached in `cache/` under a hash of the provider, model and prompt. The key is never part of the cache key or the cached file.
- **Errors.** When a model call fails, the app logs and shows only the exception type, not the request.

If you find a path where a key is logged, cached, written or sent somewhere else, treat it as a security issue and report it as above.

## Data notes

- `data/flights.csv` (the 2015 US DOT data from the challenge) is not committed.
- `runs.sqlite` (the audit log) and `cache/` are not committed. On the live site they live on the host laptop.
- Messages a visitor types into the ops inbox are stored in `runs.sqlite` (up to 240 characters each) and are sent to the model in that visitor's next live run. Don't type personal or secret information into them.
- Ops notes are treated as data, never as instructions. A note that looks like an attempt to bypass a safety rule is flagged and never becomes a rule, and every plan is checked by plain-code safety rules regardless of what the agents say. Reports of a note or prompt that gets past this are welcome.
- Gates, crew times, fuel and other operational details are synthetic and labelled as such.
