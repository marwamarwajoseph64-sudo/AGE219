import os, json
import pandas as pd
import numpy as np
from scipy import stats
from scipy.signal import savgol_filter

DATA_DIR = '/storage/emulated/0/AGE219/data'

df = pd.read_csv(os.path.join(DATA_DIR,'merged_data.csv'),
                 parse_dates=['timestamp'])
sensor_cols = ['MC_ZoneA','MC_ZoneB','MC_ZoneC','MC_ZoneD']
SAFE = 0.13
RISK = 0.14

print("=== A: NumPy Operations ===")

# A1: Convert to percentage
for col in sensor_cols:
    df[col+'_pct'] = np.multiply(df[col].values, 100.0)
print("A1: Converted MC to percentage")

# A2: Normalised Moisture Risk Index
MC_arr = df[sensor_cols].values
NMRI   = (MC_arr - SAFE) / (RISK - SAFE)
df['NMRI_max'] = np.max(NMRI, axis=1)
print(f"A2: NMRI - Mean={df['NMRI_max'].mean():.2f}, "
      f"% High Risk={(df['NMRI_max']>=1).mean()*100:.1f}%")

print("\n=== B: SciPy Operations ===")

# B1: Linear regression - annual mean MC trend
annual = df.groupby('calendar_year')['MC_mean'].mean().reset_index()
years  = annual['calendar_year'].values.astype(float)
mc_v   = annual['MC_mean'].values

slope,intercept,r,p,se = stats.linregress(years, mc_v)
print(f"B1 Linear Regression:")
print(f"   Slope    = {slope:.6f} MC/year")
print(f"   R²       = {r**2:.4f}")
print(f"   p-value  = {p:.4f}")
print(f"   Trend    = {'DECREASING' if slope<0 else 'INCREASING'}")
print(f"   Significant? {'YES' if p<0.05 else 'NO (p>=0.05)'}")

# B2: Pearson correlation
r_AC,p_AC = stats.pearsonr(df['MC_ZoneA'].values, df['MC_ZoneC'].values)
r_AB,p_AB = stats.pearsonr(df['MC_ZoneA'].values, df['MC_ZoneB'].values)
print(f"\nB2 Pearson Correlation:")
print(f"   Zone A <-> Zone B: r={r_AB:.4f}, p={p_AB:.4f}")
print(f"   Zone A <-> Zone C: r={r_AC:.4f}, p={p_AC:.4f}")

# B3: Savitzky-Golay smoothing
df_y1 = df[df['year_id']==1].copy().reset_index(drop=True)
df_y1['MC_ZoneA_smoothed'] = savgol_filter(
    df_y1['MC_ZoneA'].values, window_length=31, polyorder=3)
print(f"\nB3 Savitzky-Golay Smoothing (Year1, ZoneA):")
print(f"   Raw std   = {df_y1['MC_ZoneA'].std():.5f}")
print(f"   Smooth std= {df_y1['MC_ZoneA_smoothed'].std():.5f}")

smooth_path = os.path.join(DATA_DIR,'year1_smoothed.csv')
df_y1[['timestamp','MC_ZoneA','MC_ZoneA_smoothed']].to_csv(smooth_path, index=False)
print(f"   Saved: {smooth_path}")

# B4: One-sample t-test
t,p_t = stats.ttest_1samp(df['MC_mean'].values, popmean=SAFE)
print(f"\nB4 t-test (mean MC vs safe threshold {SAFE}):")
print(f"   t = {t:.2f},  p = {p_t:.8f}")
print(f"   {'SIGNIFICANTLY ABOVE safe threshold!' if p_t<0.05 and t>0 else 'OK'}")

# B5: Risk per year
risk_yr = df.groupby('calendar_year').apply(
    lambda g:(g['aflatoxin_risk']=='High Risk').mean()*100
).reset_index()
risk_yr.columns = ['year','pct_high_risk']
print(f"\nB5 High-Risk % per year:")
print(risk_yr.to_string(index=False))

# Save stats
stats_df = annual.copy()
stats_df.columns = ['year','mean_MC']
stats_df['pct_high_risk']      = risk_yr['pct_high_risk'].values
stats_df['regression_line_MC'] = slope*years + intercept
stats_df.to_csv(os.path.join(DATA_DIR,'stats_results.csv'), index=False)

reg = {'slope':slope,'intercept':intercept,'r_squared':r**2,'p_value':p}
with open(os.path.join(DATA_DIR,'regression_params.json'),'w') as f:
    json.dump(reg,f,indent=2)

print(f"\nSaved stats_results.csv and regression_params.json")
print("Script 02 DONE")
