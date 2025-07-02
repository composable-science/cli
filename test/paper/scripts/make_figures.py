#!/usr/bin/env python3
"""Generate figures for LaTeX paper"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

def main():
    # Ensure figures directory exists
    Path("figures").mkdir(exist_ok=True)
    
    # Load data
    data_files = list(Path("data/raw").glob("*.csv"))
    if not data_files:
        print("No CSV files found in data/raw/")
        return
    
    df = pd.read_csv(data_files[0])
    
    # Generate scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(df['temperature'], df['measurement'], alpha=0.6, s=30)
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Measurement Value')
    plt.title('Temperature vs Measurement')
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/temperature_measurement.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Generate histogram
    plt.figure(figsize=(8, 6))
    plt.hist(df['measurement'], bins=20, alpha=0.7, edgecolor='black')
    plt.xlabel('Measurement Value')
    plt.ylabel('Frequency')
    plt.title('Distribution of Measurements')
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/measurement_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Figures generated successfully!")
    print("  - figures/temperature_measurement.png")
    print("  - figures/measurement_distribution.png")

if __name__ == "__main__":
    main()
