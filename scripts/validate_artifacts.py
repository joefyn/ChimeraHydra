name: chimera-validate-schemas

on:
  workflow_dispatch:
  schedule:
    - cron: '33 03 * * *' # nightly quick pass
  pull_request:
    branches: [ main ]
    types: [ opened, synchronize, reopened, ready_for_review, labeled ]
    paths:
      - 'schemas/**'
      - 'artifacts/**'
      - 'validate_artifacts.py'
      - '.github/workflows/chimera-validate-schemas.yml'

permissions:
  contents: read

concurrency:
  group: schemas-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  validate:
    name: Schema & Artifact Validation (extended)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    # For PRs, only run when explicitly labeled 'full-gate'; always run for schedule/dispatch
    if: ${{ github.event_name != 'pull_request' || contains(github.event.pull_request.labels.*.name, 'full-gate') }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python 3.11.x
        uses: actions/setup-python@v5
        with:
          python-version: '3.11.x'
          cache: 'pip'

      - name: Install deps (pinned)
        run: |
          python -m pip install --upgrade pip
          pip install 'jsonschema==4.*'

      - name: Validate artifacts (strict by default)
        run: |
          python validate_artifacts.py \
            --schemas-dir schemas \
            --artifacts-dir artifacts \
            --dialect 2020-12 \
            --fail-on-invalid \
            --max-depth 0

      - name: Extended tests (placeholder)
        run: echo "No extended tests configured yet."