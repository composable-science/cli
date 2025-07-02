import inspect
import json
import os
from pathlib import Path
from functools import wraps

# Environment variable that the build system uses to tell the script where to save its provenance.
CS_PROVENANCE_OUTPUT = "CS_PROVENANCE_OUTPUT"

class ProvenanceTracker:
    """
    A class to track and save fine-grained provenance records from within a script.
    
    Usage:
    
    # In your script (e.g., scripts/make_figures.py)
    tracker = ProvenanceTracker()
    
    @tracker.record
    def process_data(data):
        # ...
        return processed_data
        
    # At the end of your script
    tracker.save()
    """
    
    def __init__(self):
        self.records = []
        self.output_path = os.environ.get(CS_PROVENANCE_OUTPUT)

    def record(self, func=None, *, path=None):
        """
        A decorator that records provenance for a function call.
        - If used as @tracker.record, it records the function's return value.
        - If used as @tracker.record(path="..."), it records the function as the
          creator of the specified file artifact.
        """
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                filepath = fn.__code__.co_filename
                lineno = fn.__code__.co_firstlineno

                # Execute the function
                result = fn(*args, **kwargs)

                if path:
                    log_entry = {
                        "type": "artifact",
                        "name": fn.__name__,
                        "path": path,
                        "function": fn.__name__,
                        "filepath": filepath,
                        "lineno": lineno,
                    }
                else:
                    log_entry = {
                        "type": "value",
                        "name": fn.__name__,
                        "value": "omitted" if isinstance(result, (list, dict, set)) else result,
                        "filepath": filepath,
                        "lineno": lineno,
                    }
                self.records.append(log_entry)
                
                return result
            return wrapper

        if func:
            return decorator(func)
        return decorator

    def save(self):
        """Saves the collected provenance records to the path specified by CS_PROVENANCE_OUTPUT."""
        if not self.output_path:
            # Silently do nothing if the environment variable is not set.
            # This allows scripts to run outside the `cs build` environment without error.
            return

        # Ensure the output directory exists
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "w") as f:
            json.dump({"fine_grained_provenance": self.records}, f, indent=2)

# For convenience, a default tracker can be used for simple scripts.
default_tracker = ProvenanceTracker()
record = default_tracker.record
save = default_tracker.save
