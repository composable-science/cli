#!/usr/bin/env python3
"""Generate sample data for LaTeX paper"""

import pandas as pd
import numpy as np
from pathlib import Path
from cs.provenance import record

# Create a global dataframe to be used by the decorated functions
np.random.seed(42)
n_samples = 100
temp_data = np.random.normal(25, 5, n_samples)
df = pd.DataFrame({
    'experiment_id': range(1, n_samples + 1),
    'temperature': temp_data,
    'pressure': np.random.normal(1013, 50, n_samples),
    'measurement': np.random.normal(100, 15, n_samples)
})

@record
def sample_mean():
    return np.mean(df['temperature'])

@record
def sample_std():
    return np.std(df['temperature'])

@record(path="data/raw/experiments.csv")
def save_experiments():
    """Saves the experimental data to a CSV file."""
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/raw/experiments.csv", index=False)

def main():
    # The decorated functions will automatically log their provenance when called.
    sample_mean()
    sample_std()
    save_experiments()
    
    print(f"Generated sample dataset with {len(df)} experiments")
    print("Saved to data/raw/experiments.csv")

if __name__ == "__main__":
    main()
