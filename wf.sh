#!/bin/bash

# Run export using uv
uv run python export_html.py 

# Get blog count from the JSON file using config
COUNT=$(uv run python -c "from config import Settings; import json, os; s=Settings(); path=os.path.join(s.JSON_DIR, s.CHECKPOINT_FILENAME); print(len(json.load(open(path))['discovered_blogs']))")

git add index.html .gitignore 
git commit -m "$COUNT blogs"