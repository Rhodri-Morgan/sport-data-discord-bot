APP_NAME := sport-data-discord-bot
MODULE   := sport_data_bot

DOCKER_RUN := docker run --rm \
	--name $(APP_NAME) \
	--env-file .env \
	-v $(HOME)/.aws:/root/.aws:ro \
	-e AWS_PROFILE=rtm


.PHONY: init
init:
	$(MAKE) setup-direnv
	$(MAKE) install-dev
	$(MAKE) install-git-hooks

.PHONY: setup-direnv
setup-direnv:
	@grep -q 'direnv hook zsh' ~/.zshrc 2>/dev/null || (echo '\neval "$$(direnv hook zsh)"' >> ~/.zshrc && echo "Added direnv hook to ~/.zshrc")
	direnv allow

.PHONY: install
install:
	uv sync

.PHONY: install-dev
install-dev:
	uv sync --dev

.PHONY: install-git-hooks
install-git-hooks:
	uv run pre-commit install

.PHONY: format
format:
	uv run black .

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: typecheck
typecheck:
	uv run ty check

.PHONY: run
run:
	openlogs --name bot uv run python -m $(MODULE)

.PHONY: dev
dev:
	openlogs --name bot uv run python -m $(MODULE)

.PHONY: test
test:
	openlogs --name test uv run pytest

.PHONY: ci-test
ci-test:
	uv run pytest

.PHONY: docker-stop
docker-stop:
	@docker stop $(APP_NAME) 2>/dev/null || true

.PHONY: docker-build
docker-build:
	docker build -t $(APP_NAME) .

.PHONY: docker-run
docker-run: docker-stop docker-build
	openlogs --name docker-run $(DOCKER_RUN) $(APP_NAME)

.PHONY: docker-dev
docker-dev: docker-stop docker-build
	openlogs --name docker-run $(DOCKER_RUN) $(APP_NAME)

.PHONY: docker-test
docker-test: docker-build
	openlogs --name docker-test $(DOCKER_RUN) $(APP_NAME) uv run pytest

.PHONY: docker-shell
docker-shell: docker-build
	$(DOCKER_RUN) -it $(APP_NAME) /bin/bash

.PHONY: clean
clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: docker-clean
docker-clean:
	docker rmi $(APP_NAME) 2>/dev/null || true

.PHONY: logs
logs:
	@cat .openlogs/bot.txt 2>/dev/null || cat .openlogs/test.txt 2>/dev/null || echo "No local logs found"

.PHONY: docker-logs
docker-logs:
	@cat .openlogs/docker-run.txt 2>/dev/null || cat .openlogs/docker-test.txt 2>/dev/null || echo "No docker logs found"

.PHONY: tag-and-push
tag-and-push:
	@gh api 'repos/Rhodri-Morgan/github-workflows/contents/scripts/tag-and-push.sh?ref=v2' --jq '.content' | base64 -d > /tmp/tag-and-push.sh
	@sh /tmp/tag-and-push.sh
