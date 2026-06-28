import os, json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats

DATA_DIR  = '/storage/emulated/0/AGE219/data'
PLOTS_DIR = '/storage/emulated/0/AGE219/plots'
os.makedirs(PLOTS_DIR, exist_ok=True)

df       = pd.read_csv(os.path.join(DATA_DIR,'merged_data.csv'),
                       parse_dates=['timestamp'])
stats_df = pd.read_csv(os.path.join(DATA_DIR,'stats_results.csv'))
df_sm    = pd.read_csv(os.path.join(DATA_DIR,'year1_smoothed.csv'),
                       parse_dates=['timestamp'])
with open(os.path.join(DATA_DIR,'regression_params.json')) as f:
    reg = json.load(f)

sensor_cols = ['MC_ZoneA','MC_ZoneB','MC_ZoneC','MC_ZoneD']
zone_labels = ['Zone A (Bottom)','Zone B (Middle)',
               'Zone C (Upper-Mid)','Zone D (Top)']
zone_colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728']
RISK = 0.14
SAFE = 0.13
years = stats_df['year'].values.astype(float)

plt.rcParams.update({
    'font.size':10,'axes.titlesize':12,
    'axes.titleweight':'bold','axes.grid':True,
    'grid.alpha':0.35,'grid.linestyle':'--'
})

# ── PLOT 1: Trend Line Chart ──────────────────────────────────────────────
print("Generating Plot 1 - Trend Analysis...")
annual_zone = df.groupby('calendar_year')[sensor_cols].mean().reset_index()
annual_zone.columns = ['year'] + sensor_cols

fig1, ax1 = plt.subplots(figsize=(10,6))
for col,label,color in zip(sensor_cols,zone_labels,zone_colors):
    ax1.plot(annual_zone['year'], annual_zone[col]*100,
             marker='o', linewidth=2, markersize=6,
             label=label, color=color)

trend_y = (reg['slope']*years + reg['intercept'])*100
ax1.plot(years, trend_y,'k--',linewidth=1.8,
         label=f"Overall Trend (R²={reg['r_squared']:.3f})")
ax1.axhline(RISK*100, color='red', linestyle=':',
            linewidth=1.6, label=f'Aflatoxin Threshold ({RISK*100:.0f}%)')
ax1.axhline(SAFE*100, color='orange', linestyle=':',
            linewidth=1.4, label=f'Safe Limit ({SAFE*100:.0f}%)')

ax1.set_title('10-Year Trend of Grain-Bed Moisture Content\n'
              'in Stored Maize — Four Storage Zones')
ax1.set_xlabel('Year')
ax1.set_ylabel('Moisture Content [% w.b.]')
ax1.set_xticks(annual_zone['year'])
ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
ax1.set_ylim(0, 80)
ax1.legend(loc='upper right', fontsize=8, framealpha=0.9)
txt = (f"Trend: {'↓' if reg['slope']<0 else '↑'} "
       f"{abs(reg['slope']*100):.4f}% MC/year\np={reg['p_value']:.3f}")
ax1.text(0.02,0.97,txt,transform=ax1.transAxes,va='top',fontsize=8,
         bbox=dict(boxstyle='round',facecolor='lightyellow',alpha=0.8))
plt.tight_layout()
p1 = os.path.join(PLOTS_DIR,'plot1_trend_analysis.png')
fig1.savefig(p1, dpi=300, bbox_inches='tight')
plt.close(fig1)
print(f"  Saved: {p1}")

# ── PLOT 2: Bar Chart ──────────────────────────────────────────────────────
print("Generating Plot 2 - Categorical Comparison...")
risk_by_zone = {}
for col in sensor_cols:
    risk_by_zone[col] = df.groupby('calendar_year').apply(
        lambda g:(g[col]>RISK).mean()*100).values

n  = len(annual_zone['year'])
x  = np.arange(n)
bw = 0.20

fig2, ax2 = plt.subplots(figsize=(12,6))
for i,(col,label,color) in enumerate(zip(sensor_cols,zone_labels,zone_colors)):
    offset = (i-1.5)*bw
    bars = ax2.bar(x+offset, risk_by_zone[col], width=bw,
                   label=label, color=color, alpha=0.85,
                   edgecolor='white', linewidth=0.6)
    for bar in bars:
        h = bar.get_height()
        if h > 1:
            ax2.text(bar.get_x()+bar.get_width()/2, h+0.5,
                     f'{h:.0f}%', ha='center', va='bottom', fontsize=7)

ax2.axhline(50, color='red', linestyle='--', linewidth=1.2,
            label='50% Critical Line')
ax2.set_title('Percentage of High-Risk Moisture Readings per Year\n'
              'and Storage Zone (MC > 14% Aflatoxin Threshold)')
ax2.set_xlabel('Year')
ax2.set_ylabel('High-Risk Readings [%]')
ax2.set_xticks(x)
ax2.set_xticklabels(annual_zone['year'].astype(int))
ax2.set_ylim(0, 115)
ax2.legend(fontsize=8, framealpha=0.9)
plt.tight_layout()
p2 = os.path.join(PLOTS_DIR,'plot2_categorical_comparison.png')
fig2.savefig(p2, dpi=300, bbox_inches='tight')
plt.close(fig2)
print(f"  Saved: {p2}")

# ── PLOT 3: Scatter Correlation ────────────────────────────────────────────
print("Generating Plot 3 - Correlation Plot...")
df_p   = df.iloc[::5].copy()
x_vals = df_p['MC_ZoneA'].values*100
y_vals = df_p['MC_ZoneC'].values*100

sl,ic,rv,pv,_ = stats.linregress(x_vals,y_vals)
x_line = np.linspace(x_vals.min(),x_vals.max(),200)
y_line = sl*x_line + ic

fig3, ax3 = plt.subplots(figsize=(8,7))
sc = ax3.scatter(x_vals,y_vals,
                 c=df_p['calendar_year'].values,
                 cmap='viridis', alpha=0.5, s=14, edgecolors='none')
ax3.plot(x_line, y_line,'r-',linewidth=2,
         label=f'Trend: y={sl:.3f}x+{ic:.3f}\nr={rv:.4f}, p={pv:.4f}')
ax3.axvline(RISK*100,color='#1f77b4',linestyle='--',linewidth=1.4,
            label=f'Zone A Threshold ({RISK*100:.0f}%)')
ax3.axhline(RISK*100,color='#2ca02c',linestyle='--',linewidth=1.4,
            label=f'Zone C Threshold ({RISK*100:.0f}%)')
cbar = fig3.colorbar(sc,ax=ax3,pad=0.02)
cbar.set_label('Year',fontsize=9)
ax3.set_title('Correlation: Zone A (Bottom) vs Zone C (Upper-Middle)\n'
              'Moisture Content — 10-Year Stored Maize Dataset')
ax3.set_xlabel('Zone A Moisture Content [% w.b.]')
ax3.set_ylabel('Zone C Moisture Content [% w.b.]')
ax3.legend(loc='upper left',fontsize=8,framealpha=0.9)
plt.tight_layout()
p3 = os.path.join(PLOTS_DIR,'plot3_correlation.png')
fig3.savefig(p3, dpi=300, bbox_inches='tight')
plt.close(fig3)
print(f"  Saved: {p3}")

# ── PLOT 4: Smoothed Signal ────────────────────────────────────────────────
print("Generating Plot 4 - Smoothed Signal...")
fig4, ax4 = plt.subplots(figsize=(11,5))
ax4.plot(df_sm.index, df_sm['MC_ZoneA']*100,
         color='steelblue', alpha=0.45, linewidth=0.8, label='Raw Signal')
ax4.plot(df_sm.index, df_sm['MC_ZoneA_smoothed']*100,
         color='darkred', linewidth=2.0, label='Savitzky-Golay Smoothed')
ax4.axhline(RISK*100,color='red',linestyle=':',linewidth=1.5,
            label=f'Risk Threshold ({RISK*100:.0f}%)')
ax4.axhline(SAFE*100,color='orange',linestyle=':',linewidth=1.3,
            label=f'Safe Limit ({SAFE*100:.0f}%)')
ax4.set_title('Raw vs Smoothed Moisture Signal — Year 1, Zone A\n'
              '(Savitzky-Golay Noise Reduction)')
ax4.set_xlabel('Reading Index (Sequential Measurements)')
ax4.set_ylabel('Moisture Content [% w.b.]')
ax4.legend(fontsize=8, framealpha=0.9)
plt.tight_layout()
p4 = os.path.join(PLOTS_DIR,'plot4_smoothed_signal.png')
fig4.savefig(p4, dpi=300, bbox_inches='tight')
plt.close(fig4)
print(f"  Saved: {p4}")

print("\nAll 4 plots generated. Script 03 DONE")