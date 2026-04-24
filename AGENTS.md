# sport-data-discord-bot — Agent Instructions

> **Keep this file current.** AGENTS.md is the single source of truth for how
> this project works — its architecture, conventions, and development rules.
> Update it whenever you add, change, or remove a pattern. Volatile details
> that change often (specific command names, S3 prefixes, thresholds) belong
> here or in source code.

## Project Overview

A Discord bot that surfaces live [BetFair Exchange](https://www.betfair.com.au/exchange/plus/) prediction-market probabilities via DM-only prefix commands. Built with Python 3.11+ and discord.py v2. Deployed as a single ECS Fargate task behind a health check on port 4000.

Users interact through private DMs with `!`-prefixed commands — the bot does not register any guild-level slash commands.

## User-Facing Commands

| Command         | Purpose                                                                  |
| --------------- | ------------------------------------------------------------------------ |
| `!commands`     | List available commands (pinned in the DM)                               |
| `!clear`        | Delete the bot's own messages in this DM                                 |
| `!sport`        | Interactive sport → event → market selection, then probability breakdown |
| `!motorsport`   | Shortcut to Motor Sport                                                  |
| `!rugby`        | Shortcut to Rugby Union                                                  |
| `!football`     | Shortcut to Soccer                                                       |

The bot is stateless — it does not persist anything per-user. Each request is satisfied with a fresh BetFair query.

## Key Patterns

- **Docker-first**: all development and testing should be done through Docker. Use `make docker-*` targets for building, running, and testing. Local targets exist as a fallback but Docker is the preferred workflow.
- **Single-cog prefix-command model**: all user-facing commands live on one `SportCommands` cog inside `src/sport_data_bot/bot.py`. DM-only — every handler returns early if `ctx.channel.type != ChannelType.private`.
- **DM-scoped menus**: multi-step selection flows (`!sport`) use `bot.wait_for("message", ...)` with a 120s timeout against a DM channel predicate. Always offer an `exit` escape and validate input.
- **Stateless, S3-bootstrapped**: the bot keeps no per-user state. The BetFair TLS client certs (`client-2048.crt`, `client-2048.key`) live in the shared `prod-eu-west-1-app-data` S3 bucket under the `sport-data-discord-bot/` prefix and are downloaded into `certifications/` at boot. Nothing is written back to S3.
- **Task-role AWS auth**: in prod, boto3 picks up the ECS task role automatically — no static AWS keys in the container. Locally the default credential chain (`~/.aws`, env vars, direnv) applies.
- **Async HTTP-less**: unlike cogs that hit JSON APIs, this bot uses `betfairlightweight`'s synchronous client. Heavy work inside an `async with ctx.typing():` block is acceptable since the bot only serves DMs.
- **Config via env vars**: all secrets and tunables come from environment variables — see `src/sport_data_bot/config.py`. Never hardcode tokens or bucket names.

### Environment Variables

| Variable                | Purpose                                                  |
| ----------------------- | -------------------------------------------------------- |
| `DISCORD_BOT_TOKEN`     | Discord bot token                                        |
| `BETFAIR_USERNAME`      | BetFair Exchange account username                        |
| `BETFAIR_PASSWORD`      | BetFair Exchange account password                        |
| `BETFAIR_LIVE_APP_KEY`  | BetFair Live App Key                                     |
| `AWS_BUCKET_NAME`       | Shared S3 bucket (objects live under `sport-data-discord-bot/`) |
| `AWS_REGION`            | Region of the bucket (default `eu-west-1`)               |
| `HEALTH_PORT`           | Health-check HTTP port (default `4000`)                  |

In prod, AWS credentials come from the ECS task role — no static keys are passed to the container. Locally the `.envrc` (auto-loaded by direnv) pulls `DISCORD_BOT_TOKEN` from `local-sports-data-discord-bot` and `BETFAIR_*` from `prod-eu-west-1-betfair`, then writes a `.env` file consumed by `make docker-*`.

## Development

### Prerequisites

- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://www.docker.com/)
- [Node.js](https://nodejs.org/) (for openlogs)
- [openlogs](https://github.com/charlietlamb/openlogs)
- [direnv](https://direnv.net/) (auto-loads secrets from AWS Secrets Manager via `.envrc`)

### Setup

```bash
make init              # direnv hook, secrets, dev deps, git hooks
make docker-dev        # run the bot in Docker
```

Install git hooks in each clone with `make install-git-hooks`. The pre-commit hook runs `black` first and then `ruff check` without automatic fixes.

### Makefile Targets — Docker (preferred)

All Docker targets mount `.env` and `~/.aws` (read-only, `AWS_PROFILE=rtm`).

| Target              | Description                                    |
| ------------------- | ---------------------------------------------- |
| `make docker-build` | Build the Docker image                         |
| `make docker-run`   | Build + run the bot in Docker                  |
| `make docker-dev`   | Build + run the bot (full dev workflow)        |
| `make docker-test`  | Run pytest in Docker                           |
| `make docker-logs`  | Print latest docker bot/test logs              |
| `make docker-shell` | Interactive bash shell in the container        |
| `make docker-clean` | Remove the Docker image                        |

### Makefile Targets — Local (fallback)

| Target                   | Description                     |
| ------------------------ | ------------------------------- |
| `make init`              | Setup direnv, deps, git hooks   |
| `make install`           | Install production deps via uv  |
| `make install-dev`       | Install dev deps via uv         |
| `make install-git-hooks` | Install the git pre-commit hook |
| `make format`            | Run Black formatting locally    |
| `make lint`              | Run Ruff linting locally        |
| `make typecheck`         | Run ty type checking locally    |
| `make run`               | Run the bot locally             |
| `make dev`               | Run the bot locally             |
| `make test`              | Run pytest locally              |
| `make clean`             | Remove .venv and caches         |

### Adding a New Command

1. Open `src/sport_data_bot/bot.py` and add a method to the `SportCommands` cog decorated with `@commands.command(name="your_command")`.
2. Return early if `ctx.channel.type != ChannelType.private` — commands are DM-only.
3. If your command needs a wait-for-input loop, reuse `_menu_selection()` so the 120s timeout / `exit` escape behaviour is consistent.
4. If your command calls BetFair, reuse the `self.bot.betfair` client — do not create a second session.
5. **Update `README.MD` and this file** — add your new command to the User-Facing Commands table above.

### Test-Driven Development

This project follows **strict TDD**. For every new feature:

1. **Write tests first** — before implementing any feature or BetFair integration, write failing tests that define the expected behaviour.
2. **Verify the tests fail** — run `make test` to confirm they fail for the right reason.
3. **Implement the feature** — write the minimum code to make the tests pass.
4. **Run tests again** — confirm everything passes before moving on.

**This is mandatory.** Do not implement features without writing tests first. Do not skip edge cases.

**Mock data must match real API responses.** Tests that involve the BetFair API must inspect the real API response shapes (via the BetFair developer portal or `betfairlightweight` documentation) so mocked payloads line up with what the client will actually return. This prevents drift between mocks and real API responses.

Tests live in `tests/` and mirror the source structure:

- **Command logic tests** — menu flow, validation, DM gating, user-commands state transitions
- **Formatting tests** — probability string formatting, embed content
- **Graph tests** — `GraphProducer` edge cases (empty data, all-NaN data, single runner)
- **API integration tests** — real HTTP calls behind feature flags, verifying BetFair response shapes

### Development Workflow

For any code change, run formatting and linting before considering the work complete.

Local workflow:

```bash
make format
make lint
make typecheck
make test
```

`make format` and `make lint` must pass. Run `make test` as part of normal development validation. The pre-commit hook enforces `black` and `ruff check`, but do not rely on commit-time feedback as the first signal.

### Docker Build Caching

When changing the Docker build, preserve effective layer caching for CI.

- Use `tools/check_docker_cache.sh` to simulate two separate CI-style Buildx runs and verify that the second build reuses cached layers.
- Run this script after any meaningful change to `Dockerfile`, build-time dependencies, or Docker build inputs that could affect cache behavior.
- Treat cache regressions as real issues. If dependency-install or other expensive layers stop caching between runs, adjust the Dockerfile before considering the work complete.

### Documentation Standards

Use **PEP 257** as the baseline for Python docstrings in this repository.

- Add docstrings to public modules, public classes, public functions, and public methods.
- Use **Google-style docstrings** when documenting arguments, return values, raised exceptions, or side effects.
- Keep one-line docstrings for simple, self-explanatory APIs.
- Use multi-line docstrings when behavior, inputs, outputs, or edge cases need explanation.
- Write docstrings in the imperative mood and describe what the object does.
- Prefer documenting behavior and constraints over repeating type hints or obvious implementation details.
- Do not add docstrings to trivial private helpers unless the logic is non-obvious, the function has important side effects, or the helper encodes domain-specific assumptions.
- When a prefix command or scheduled task has non-obvious Discord-specific behavior (DM-only gating, pinning, thread semantics), document the operational constraint clearly in the docstring.
- Keep docstrings up to date when behavior changes.

## Deployment

The bot is deployed as a single ECS Fargate service in the `prod-eu-west-1-main` cluster. CI/CD is three workflows calling shared composite actions from `Rhodri-Morgan/github-workflows@v2`:

| Workflow           | Trigger                 | What it does                                                 |
| ------------------ | ----------------------- | ------------------------------------------------------------ |
| `test.yaml`        | `pull_request` → master | Build the image and run `make ci-test` inside it             |
| `build-push.yaml`  | Tag push `v*.*.*`       | Build the image, run tests, push to ECR with the tag name    |
| `deploy.yaml`      | `workflow_dispatch`     | Update the SSM image-tag parameter and force a new ECS rollout |

Infrastructure (ECR repo, ECS service, IAM task/execution roles, S3 bucket + policy, SSM image-tag parameter, GitHub OIDC role) lives in the `terraform` repo under `applications/` and `github/`.

## Repository Layout

```
src/sport_data_bot/
├── __init__.py
├── __main__.py          # python -m sport_data_bot entry point
├── bot.py               # SportDataBot + SportCommands cog
├── config.py            # Settings dataclass loaded from env
├── health.py            # aiohttp /health server
├── betfair_api.py       # betfairlightweight wrapper
├── aws_s3.py            # S3 downloader for BetFair TLS certs (sport-data-discord-bot/ prefix)
└── graph_producer.py    # Matplotlib chart rendering
sources/
└── Whitney Medium.ttf   # Chart font (read via os.getcwd())
.github/workflows/
├── test.yaml
├── build-push.yaml
└── deploy.yaml
tests/                   # pytest
tools/
└── check_docker_cache.sh
Dockerfile
Makefile
pyproject.toml
```
