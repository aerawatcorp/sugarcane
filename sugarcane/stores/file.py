import os
from stores import BaseStore


class FileStore(BaseStore):
    def __init__(self, config):
        # Get file path from config or define a default
        self.file_path = config.get("file_path", "data.log")  # Default to 'data.log'

    def store(self, data):
        oid, ts, flattened_annotations = self.generate_annotations(flat=True)
        # Ensure directory exists
        os.makedirs(
            os.path.dirname(self.file_path), exist_ok=True
        )  # Create directory if needed

        # Open file in append mode
        with open(self.file_path, "a") as f:
            # Write data to the file
            f.write(
                f"{flattened_annotations} :: {data}\n"
            )  # Add newline character after each entry

        return True, dict(oid=oid, ts=ts)

    def get(self, oid):
        raise NotImplementedError

    def retrieve(self, filters=None):
        # Read data from file
        try:
            with open(self.file_path, "r") as f:
                # Return list of lines (data entries)
                return f.readlines()
        except FileNotFoundError:
            # Handle missing file
            return []
