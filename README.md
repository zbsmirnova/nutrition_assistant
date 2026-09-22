# Nutrition assistant

A personal Telegram nutrition assistant for food, recipes, one daily body weight, and daily steps. Food is saved continuously; the optional daily check-in records completeness and invites missing activity.

This foundation provides strict parser, command, and outcome contracts, generated JSON Schemas, 20 authored examples, and 32 contract checks. Persistence and Telegram transport are the next implementation slices. Authored examples are expected outputs, not live-model evaluation.

## Contract development

Run from the repository root with Python 3.12+ (verified with Python 3.14.0):

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-contracts.txt
.venv/bin/python -m unittest discover -s tests -v
~~~

After changing the Python contract models, regenerate their schemas and rerun the checks:

~~~sh
.venv/bin/python -m nutrition_contracts.export
~~~

The existing deployment configuration describes Open WebUI; it does not deploy a nutrition backend.
