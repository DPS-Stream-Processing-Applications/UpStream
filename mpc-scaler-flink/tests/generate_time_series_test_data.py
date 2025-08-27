import json

import numpy as np


# Function to normalize values between 0 and 1
def normalize_series(values):
    min_val = np.min(values)
    max_val = np.max(values)
    normalized_values = (values - min_val) / (max_val - min_val)
    return normalized_values.tolist()

# Function to generate a simple linear time series
def generate_linear_series(length, gradient, noise_level=0, discrete=True):
    time = np.arange(length)
    values = gradient * time + np.random.normal(0, noise_level, size=length)
    if discrete:
        values = np.round(values).astype(int)
    return normalize_series(values)  # Normalize and return as list

# Function to generate a convex quadratic time series (y = ax^2 + bx + c)
def generate_quadratic_series(length, a, b=0, c=0, noise_level=0, discrete=True):
    time = np.arange(length)
    values = a * time**2 + b * time + c + np.random.normal(0, noise_level, size=length)
    if discrete:
        values = np.round(values).astype(int)
    return normalize_series(values)  # Normalize and return as list

# Function to generate a simple sinusoidal time series
def generate_sinusoidal_series(length, amplitude, frequency, phase=0, noise_level=0, discrete=True):
    time = np.arange(length)
    values = amplitude * np.sin(frequency * time + phase) + np.random.normal(0, noise_level, size=length)
    if discrete:
        values = np.round(values).astype(int)
    return normalize_series(values)  # Normalize and return as list

# Function to generate a gradually ascending sinusoidal series (y = mx + A * sin(wt + phi))
def generate_ascending_sinusoidal_series(length, gradient, amplitude, frequency, phase=0, noise_level=0, discrete=True):
    time = np.arange(length)
    linear_part = gradient * time
    sinusoidal_part = amplitude * np.sin(frequency * time + phase)
    values = linear_part + sinusoidal_part + np.random.normal(0, noise_level, size=length)
    if discrete:
        values = np.round(values).astype(int)
    return normalize_series(values)  # Normalize and return as list

def create_test_time_series():
    time_series_data = {}

    time_series_data["linear_series"] = {
        "description": "Simple linear function",
        "data": generate_linear_series(length=50, gradient=2, noise_level=1),
    }

    time_series_data["convex_quadratic_series"] = {
        "description": "Convex quadratic function (y = 0.05x^2)",
        "data": generate_quadratic_series(length=50, a=0.05, b=0, c=0, noise_level=1),
    }

    time_series_data["sinusoidal_series"] = {
        "description": "Sinusoidal function",
        "data": generate_sinusoidal_series(length=50, amplitude=10, frequency=0.2, phase=0, noise_level=1),
    }

    time_series_data["ascending_sinusoidal_series"] = {
        "description": "Gradually ascending sinusoidal function (y = 0.2x + 5sin(0.2x))",
        "data": generate_ascending_sinusoidal_series(length=50, gradient=0.2, amplitude=5, frequency=0.2, phase=0, noise_level=1),
    }

    return time_series_data

def main():
    time_series_set = create_test_time_series()
    print("generated time_series_set")

    with open("test_time_series.json", "w") as f:
        json.dump(time_series_set, f, indent=4)

