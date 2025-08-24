import os
import sys
import json

# lägg till projektroten i import-sökvägen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

openapi = app.openapi()
json.dump(openapi, sys.stdout, indent=2)
