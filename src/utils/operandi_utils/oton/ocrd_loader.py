import json
import os



def load_ocrd_processors():
    """Load and return json content from ocrd_all_tool.json."""
    # Get the directory of the current file
    current_dir = os.path.dirname(__file__)
    # Construct the path to ocrd_all_tool.json
    json_path = os.path.join(current_dir, "ocrd_all_tool.json")

    # Open and load the JSON file
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data