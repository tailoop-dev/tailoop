#!/usr/bin/env bash
# Installs the Tailoop release named by TAILOOP_VERSION the way a customer does:
# with pip, from Tailoop's package index. Run by .github/workflows/regression.yml.
set -euo pipefail

: "${TAILOOP_INDEX_URL:?is not set}"

# Typed by hand in the Run workflow form
version="${TAILOOP_VERSION:-latest}"
version="${version//[[:space:]]/}"
if [[ "$version" == "latest" ]]; then
  requirement="tailoop"
elif [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(rc[0-9]+)?$ ]]; then
  requirement="tailoop==$version"
else
  echo "::error::The version must be latest or a release, such as 1.0.0 or 1.0.0rc1."
  exit 1
fi

# Tailoop comes from its own index and its dependencies from PyPI, where the name
# "tailoop" is ours, so no one else's package can take its place.
pip install --index-url "$TAILOOP_INDEX_URL" --extra-index-url https://pypi.org/simple/ \
  "$requirement"
# When the index gives nothing, pip settles for PyPI's placeholder, which has no command.
if ! command -v tailoop > /dev/null; then
  echo "::error::No Tailoop came from its index: check the TAILOOP_INDEX_URL secret," \
    "and that the release exists."
  exit 1
fi
tailoop version

# Later steps report the version that ran, also when "latest" was asked for.
installed=$(python -c 'from importlib.metadata import version; print(version("tailoop"))')
if [[ -n "${GITHUB_ENV:-}" ]]; then
  echo "TAILOOP_VERSION=$installed" >> "$GITHUB_ENV"
fi
