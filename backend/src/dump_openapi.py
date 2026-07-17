import json
import sys
from main import app

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f)
