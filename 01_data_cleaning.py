import os, glob
import pandas as pd
import numpy as np

DATA_DIR  = '/storage/emulated/0/AGE219/data'
OUT_DIR   = '/storage/emulated/0/AGE219/data'

print("Loading CSV files...")
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, 'Year*.csv')))
print(f"Found {len(csv_files)} files")

frames = []
for i, filepath in enumerate(csv_files, start=1):
    df_temp = pd.read_csv(filepath)
    df_temp['year_id'] = i
    df_temp['source_file'] = os.path.basename(filepath)
    frames.append(df_temp)
    print(f"  Loaded {os.path.basename(filepath)} -> {df_temp.shape[0]} rows")

df = pd.concat(frames, ignore_index=True)
print(f"\nCombined shape: {df.shape}")

# Clean
sensor_cols = ['moisture0','moisture1','moisture2','moisture3']
df.dropna(subset=sensor_cols, inplace=True)
for col in sensor_cols:
    df = df[(df[col] >= 0.0) & (df[col] <= 1.0)]

# Fix types
for c in ['month','day','hour','minute','second']:
    df[c] = df[c].astype(int)

# Add calendar year (Year1=2015 ... Year10=2024)
BASE_YEAR = 2015
df['calendar_year'] = BASE_YEAR + (df['year_id'] - 1)

# Build timestamp
df['timestamp'] = pd.to_datetime({
    'year'  : df['calendar_year'],
    'month' : df['month'],
    'day'   : df['day'],
    'hour'  : df['hour'],
    'minute': df['minute'],
    'second': df['second']
})

# Rename sensors
df.rename(columns={
    'moisture0':'MC_ZoneA',
    'moisture1':'MC_ZoneB',
    'moisture2':'MC_ZoneC',
    'moisture3':'MC_ZoneD'
}, inplace=True)
sensor_cols = ['MC_ZoneA','MC_ZoneB','MC_ZoneC','MC_ZoneD']

# New features
df['MC_mean'] = df[sensor_cols].mean(axis=1)
df['aflatoxin_risk'] = (df[sensor_cols].max(axis=1) > 0.14).map(
    {True:'High Risk', False:'Safe'})

print(f"\nFinal shape: {df.shape}")
print("\nRisk summary:")
print(df['aflatoxin_risk'].value_counts())

print("\nPer-year mean MC:")
print(df.groupby('calendar_year')[sensor_cols+['MC_mean']].mean().round(4))

out = os.path.join(OUT_DIR, 'merged_data.csv')
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
print("Script 01 DONE")