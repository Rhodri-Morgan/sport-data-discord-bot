# Sport Data Discord Bot

![deployed.png](https://img.shields.io/badge/-Deployed-green)

A Discord bot that pulls live odds from [BetFair Exchange](https://www.betfair.com.au/exchange/plus/) and DMs you implied probabilities for any sport, event, and market — with a runner-by-runner breakdown, bar and pie charts, and a market-efficiency score. Works across motor sport, rugby union, football, and anything else trading on the Exchange. Stateless: every request is a fresh query.

## Quick Start (Docker)

```bash
direnv allow          # loads secrets from AWS Secrets Manager and writes .env
make docker-run
```

## Prerequisites

- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://www.docker.com/)
- [Node.js](https://nodejs.org/) (for openlogs)
- [openlogs](https://github.com/charlietlamb/openlogs)
- [direnv](https://direnv.net/) (auto-loads secrets via `.envrc`)
- [AWS CLI](https://aws.amazon.com/cli/) and [jq](https://stedolan.github.io/jq/) (used by `.envrc` to fetch secrets)

## Quick Start (Local)

```bash
direnv allow
make install-dev
make install-git-hooks
make run
```

Git commits run `black` and `ruff` through a pre-commit hook once installed.

## Commands

DM-only — the bot ignores any message in a guild channel.

| Command       | Description                                                                |
| ------------- | -------------------------------------------------------------------------- |
| `!commands`   | Pin a list of available commands in the DM                                 |
| `!clear`      | Delete the bot's own messages in the current DM                            |
| `!sport`      | Interactive sport → event → market selector with probability breakdown     |
| `!motorsport` | Shortcut to Motor Sport                                                    |
| `!rugby`      | Shortcut to Rugby Union                                                    |
| `!football`   | Shortcut to Soccer                                                         |

The bot is stateless — each request issues a fresh BetFair query.

## Configuration

| Variable               | Required | Default     | Description                                                          |
| ---------------------- | -------- | ----------- | -------------------------------------------------------------------- |
| `DISCORD_BOT_TOKEN`    | Yes      | —           | Discord bot token                                                    |
| `BETFAIR_USERNAME`     | Yes      | —           | BetFair Exchange account username                                    |
| `BETFAIR_PASSWORD`     | Yes      | —           | BetFair Exchange account password                                    |
| `BETFAIR_LIVE_APP_KEY` | Yes      | —           | BetFair Live App Key                                                 |
| `AWS_BUCKET_NAME`      | Yes      | —           | S3 bucket holding BetFair TLS certs under `sport-data-discord-bot/`  |
| `AWS_REGION`           | No       | `eu-west-1` | Region of the bucket                                                 |
| `HEALTH_PORT`          | No       | `4000`      | Health-check HTTP port                                               |

In prod, AWS credentials come from the ECS task role. Locally, `.envrc` pulls `DISCORD_BOT_TOKEN` from `local-sports-data-discord-bot` and `BETFAIR_*` from `prod-eu-west-1-betfair`, then writes a `.env` file consumed by `make docker-*`.

## Makefile Targets

| Target                   | Description                        |
| ------------------------ | ---------------------------------- |
| `make docker-run`        | Build + run the bot in Docker      |
| `make docker-dev`        | Build + run the bot                |
| `make docker-test`       | Run pytest in Docker               |
| `make docker-logs`       | Print latest docker bot/test logs  |
| `make docker-build`      | Build the Docker image             |
| `make docker-shell`      | Interactive shell in the container |
| `make install-git-hooks` | Install the git pre-commit hook    |
| `make run`               | Run the bot locally                |
| `make test`              | Run pytest locally                 |

## Project Structure

See [AGENTS.md](AGENTS.md) for architecture, patterns, and contributing conventions.
