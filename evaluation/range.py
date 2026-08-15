import sys

import pandas as pd

path = sys.argv[1]
ts = pd.read_parquet(path, columns=["timestamp"])["timestamp"]
print(f"First: {ts.min()}")
print(f"Last:  {ts.max()}")
