#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: tools/check_docker_cache.sh [options]

Simulate two separate CI builds using Docker Buildx cache export/import and
report how effectively the second build reuses cached layers.

Options:
  --dockerfile PATH    Dockerfile path (default: Dockerfile)
  --context PATH       Build context path (default: .)
  --image NAME         Local image name to build (default: cache-check)
  --cache-root PATH    Directory for cache artifacts/logs
                       (default: .tmp/docker-cache-check)
  --target NAME        Optional Docker target
  --build-arg KEY=VAL  Repeatable build arg
  --secret ID=VALUE    Repeatable BuildKit secret
  --keep-artifacts     Keep cache/log directories instead of deleting them first
  --help               Show this help
EOF
}

dockerfile="Dockerfile"
context="."
image_name="cache-check"
cache_root=".tmp/docker-cache-check"
target=""
keep_artifacts="false"
build_args=()
secrets=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dockerfile)
      dockerfile="$2"
      shift 2
      ;;
    --context)
      context="$2"
      shift 2
      ;;
    --image)
      image_name="$2"
      shift 2
      ;;
    --cache-root)
      cache_root="$2"
      shift 2
      ;;
    --target)
      target="$2"
      shift 2
      ;;
    --build-arg)
      build_args+=("$2")
      shift 2
      ;;
    --secret)
      secrets+=("$2")
      shift 2
      ;;
    --keep-artifacts)
      keep_artifacts="true"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "docker buildx is required" >&2
  exit 1
fi

if [[ ! -f "$dockerfile" ]]; then
  echo "Dockerfile not found: $dockerfile" >&2
  exit 1
fi

if [[ "$keep_artifacts" != "true" ]]; then
  rm -rf "$cache_root"
fi

log_dir="$cache_root/logs"
cache_run1="$cache_root/cache-run1"
cache_run2="$cache_root/cache-run2"
mkdir -p "$log_dir"

builder_one="cache-check-$(date +%s)-1"
builder_two="cache-check-$(date +%s)-2"

cleanup() {
  docker buildx rm "$builder_one" >/dev/null 2>&1 || true
  docker buildx rm "$builder_two" >/dev/null 2>&1 || true
}

trap cleanup EXIT

common_args=(
  --progress=plain
  --file "$dockerfile"
  --tag "local/${image_name}:cache-check"
  --load
)

if [[ -n "$target" ]]; then
  common_args+=(--target "$target")
fi

if [[ ${#build_args[@]} -gt 0 ]]; then
  for build_arg in "${build_args[@]}"; do
    common_args+=(--build-arg "$build_arg")
  done
fi

if [[ ${#secrets[@]} -gt 0 ]]; then
  for secret in "${secrets[@]}"; do
    common_args+=(--secret "id=${secret%%=*},env=${secret%%=*}")
  done
fi

run_build() {
  local builder_name="$1"
  local log_file="$2"
  shift 2

  docker buildx create --name "$builder_name" --use >/dev/null
  {
    /usr/bin/time -p docker buildx build "${common_args[@]}" "$@" "$context"
  } 2>&1 | tee "$log_file"
}

echo "==> First build: cold cache"
run_build \
  "$builder_one" \
  "$log_dir/first-build.log" \
  --cache-to "type=local,dest=${cache_run1},mode=max"

echo
echo "==> Second build: restored cache in fresh builder"
run_build \
  "$builder_two" \
  "$log_dir/second-build.log" \
  --cache-from "type=local,src=${cache_run1}" \
  --cache-to "type=local,dest=${cache_run2},mode=max"

cached_steps=$(grep -c ' CACHED$' "$log_dir/second-build.log" || true)
done_steps=$(grep -c ' DONE [0-9]' "$log_dir/second-build.log" || true)
first_time=$(awk '/^real / {print $2}' "$log_dir/first-build.log" | tail -n1)
second_time=$(awk '/^real / {print $2}' "$log_dir/second-build.log" | tail -n1)

echo
echo "==> Cache summary"
echo "First build time:  ${first_time:-unknown}s"
echo "Second build time: ${second_time:-unknown}s"
echo "Cached steps:      $cached_steps"
echo "Non-cached steps:  $done_steps"
echo "Logs:              $log_dir"

if [[ "$cached_steps" -eq 0 ]]; then
  echo
  echo "Cache check failed: second build did not report any cached steps." >&2
  exit 1
fi

echo
echo "Cache check passed: second build reused cached layers."
