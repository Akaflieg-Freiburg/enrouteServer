# Contributing to enrouteServer

Thank you for helping to improve the maps of Enroute Flight Navigation! This page explains how contributions work. For an overview of the code, read [docs/architecture.md](docs/architecture.md) first.

## Ways to contribute

- **Report a problem or request a region:** open an [issue](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/new/choose) and pick the matching template. Data errors are best fixed upstream at openAIP or open flightmaps; see the [README](README.md#missing-a-country-or-found-wrong-data).
- **Add a region, chart or VAC collection:** follow the how-tos in [docs/howto/](docs/README.md#run-and-contribute). These are usually small changes to a list at the top of one script.
- **Improve a script:** fix a bug, speed something up, or improve the output.
- **Improve the documentation:** if something in `docs/` was wrong or unclear to you, fix it. That is a very welcome contribution.

## Workflow

1. Fork the repository and create a branch from `main`.
2. [Set up a working copy](docs/setup.md). You can run all generators without server credentials; do not run `deploy-hetzner.py`.
3. Make your change and **test it on one region**, e.g. `python3 splitAviationMap.py Slovenia` or `python3 generateRasterMaps.py Slovenia`. Inspect the result in `scripts/out/`.
4. If you touched documentation, run `python3 .github/check-docs.py` from the repository root. It checks links and that every script is documented; the same check runs automatically on every pull request.
5. Open a pull request against `main`. Describe what you changed and how you tested it. The PR template contains a short checklist.

The maintainer runs the production pipeline and deploys. Your change goes live with the next production run after merging.

## Rules

- **Documentation changes go in the same pull request as the code.**
  - If you change what a script reads, writes or accepts as arguments, update [docs/scripts.md](docs/scripts.md).
  - If you change an output format, update the specification in [docs/formats/](docs/formats/README.md). Format changes affect every installed app, so read ["Changing a format"](docs/formats/README.md#changing-a-format) first.
- **Keep output deterministic.** Serialize JSON with `sort_keys=True, separators=(',', ':')`. The deploy step relies on unchanged data producing identical files.
- **Run scripts from inside `scripts/`.** They use relative paths.
- **Never commit generated data.** `scripts/out/`, `scripts/staging/`, `scripts/data/` and the `*_storage/` caches are ignored by git.
- **Respect data licenses.** Only add sources that allow redistribution, and keep attributions intact.
- **Docstrings:** library modules (`OFMX.py`, `openAIP2.py`, `vector_tile.py`, …) use reStructuredText docstrings with `:param:` and `:returns:`. Every script should start with a module docstring that says what it does and how to call it.

## Questions

Open an issue, or ask in the pull request. There are no stupid questions; they show where the documentation needs to improve.
