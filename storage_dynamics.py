import numpy as np
import random
import pandas as pd
import matplotlib.pyplot as plt
import glob
import seaborn as sns
import os

sns.set_theme()
sns.set_style("white")
# Get cwd code thanks to https://thispointer.com/python-how-to-get-the-current-working-directory/
# Modify filenames and locations depending on test case ############
cwd = os.getcwd()
storage_filename = cwd + "/dynamics/str_dynamics/str_dynamics_1.0_0.01.csv"
demand_filename = cwd + "/dynamics/restr_demand/restr_demand_1.0_0.01.csv"
rf_filename = cwd + "/dynamics/restr_freq/restr_freq_1.0_0.01.csv"
risk_filename = cwd + "/dynamics/short_term_risk/risk_1.0_0.01.csv"

storage = np.loadtxt(storage_filename, delimiter = ",")
restr_demand = np.loadtxt(demand_filename, delimiter = ",")
restr_freq = np.loadtxt(rf_filename, delimiter = ",")
rof = np.loadtxt(risk_filename, delimiter=",")

r = 0

# conduct SSI6 on the inflows
def meets_conditions(window):
  three_month = True
  hits_negative = False
  for i in range(len(window)):
    if window[i] > 0:
      three_month = False
      break
    else:
      continue

  for i in range(len(window)):
    if window[i] <= -1:
      hits_negative = True
      break
    else:
      continue

  if (three_month + hits_negative == 2):
    return 1
  else:
    return 0

def find_droughts(realization):
  droughts = []
  for i in range(len(realization) - 12):
    window = realization[i: i+12]
    if meets_conditions(window) == 1:
      info = {}
      info['start'] = i
      info['end'] = i + 11
      info['severity'] = np.sum(window)
      droughts.append(info)
  return droughts

demand_file = cwd + "/water_balance_files/cary_demand.csv"
inflow_file = cwd + "/water_balance_files/jordan_lake_inflows.csv"

inflows = 0.20*np.loadtxt(inflow_file, delimiter=",")
demand = 1.1*np.loadtxt(demand_file, delimiter=",")
sp = inflows.shape[1] - demand.shape[1] + 52
inflow_r = pd.DataFrame(np.log(inflows[r, sp:]).flatten()).fillna(method='pad')
mu = inflow_r.mean()
sigma = inflow_r.std()
Z_k = (inflow_r - mu) / sigma
rolling_avg = (Z_k.rolling(24, min_periods=1).mean()).fillna(method='pad')
ssi6 = (rolling_avg.to_numpy()).flatten()
print("ssi6 = ", ssi6)
droughts = find_droughts(ssi6)
# SSI6 ends here

years = np.arange(0,2340,1)
alpha = 0.05
storage_r = storage[r,:]/(10**3)
rd_r = restr_demand[r,:]/(10**3)
rf_r = restr_freq[r,:]
rof_r = rof[r,:]*100

restriction_year = []
for i in range(len(rof_r)):
    if rf_r[i] == 1:
        restriction_year.append(years[i])

fig, ax = plt.subplots(2,1, figsize=(12,6))
year_strings = (np.arange(2020, 2080, 15)).astype(str)
yr = np.arange(0,2341,780)
#print(len(year_strings))
#print(len(yr))
ax[0].vlines(x=restriction_year, ymin=0, ymax=100, color="maroon", linewidth=1.2, label="restrictions")
ax[0].hlines(y=1, xmin=0, xmax=2340, linewidth=1.2, color="crimson", linestyle=(0,(5,10)), label=r"$\alpha$ = 1%")
ax[0].plot(years, rof_r, color="orange", linewidth=1.5, label="ROF values", )

#ax[0].set_xlabel("Year",fontsize=14)
ax[0].set_xticks(yr)
ax[0].set_xticklabels(year_strings, fontsize=14)
ax[0].set_ylabel("% Risk",fontsize=14)
ax2=ax[0].twinx()
ax2.plot(years, storage_r, color="royalblue", linewidth=1.2, label="Storage (BG)")
ax2.set_ylabel("Storage (BG)")

ax[1].plot(years, ssi6, color="black", label=r"$SSI_{6}$")
for drought in find_droughts(ssi6):
  ax[1].axvspan(drought['start'], drought['end'], facecolor='indianred', edgecolor='none', alpha=0.4)
ax[1].set_xlabel("Year",fontsize=14)
ax[1].set_ylabel(r"$SSI_{6}$")
ax[1].set_xticks(yr)
ax[1].set_xticklabels(year_strings, fontsize=14)

plt.suptitle(r"Storage dynamics over time ($\alpha$ = 1%)")
handles, labels = [(a + b + c) for a, b, c in zip(ax[0].get_legend_handles_labels(), ax2.get_legend_handles_labels(), ax[1].get_legend_handles_labels())]
ax[1].legend(handles, labels, loc="upper right")
fig.tight_layout()
plt.savefig("Figures/storage_dynamics_001.png")
plt.show()
