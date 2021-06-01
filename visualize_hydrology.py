import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

sns.set_theme()
sns.set_style("darkgrid")
# Get cwd code thanks to https://thispointer.com/python-how-to-get-the-current-working-directory/
# Modify filenames and locations depending on test case ############
cwd = os.getcwd()
evap_file = cwd + "\water_balance_files\jordan_lake_evap.csv"
inflow_file = cwd + "\water_balance_files\jordan_lake_inflows.csv"
demand_file = cwd + "\water_balance_files\cary_demand.csv"

# Load .csv files  ##################################################
evap = 2*np.loadtxt(evap_file, delimiter=",")
inflows = 0.20*np.loadtxt(inflow_file, delimiter=",")
demand = 1.1*np.loadtxt(demand_file, delimiter=",")

# Helper functions ##################################################
def calc_storage(s_t, e_t, i_t, d_t):
    s_tnext = s_t - e_t + i_t - d_t
    if (s_tnext/reservoir_capacity) >= 1.0:
        return reservoir_capacity
    elif s_tnext < 0:
        return 0.0
    else:
        return s_tnext

# Fixed values ######################################################
reservoir_capacity = 14900*0.5
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary"
n_sym_years = int(demand.shape[1] / n_weeks)
n_sym_weeks = int(demand.shape[1])

storage_arr = np.zeros((demand.shape[0], demand.shape[1] - 52))
sp = inflows.shape[1] - demand.shape[1] + 52

s0 = reservoir_capacity*0.4
storage_arr[:,0] = s0
for i in range(storage_arr.shape[0]):
    for j in range(1,storage_arr.shape[1]):
        storage_arr[i, j] = calc_storage(storage_arr[i,j-1], evap[i,j+sp-1], inflows[i,j+sp-1], demand[i,j+52-1])
np.savetxt("storage_arr.csv", storage_arr, delimiter=",")

inf = inflows[:, sp:]
weeks = np.arange(0, len(inf[1,:]), 1)
years = np.arange(0,2340,1)
year_strings = (np.arange(2020, 2080, 15)).astype(str)
yr = np.arange(0,2341,780)

fig, ax = plt.subplots(3,1,figsize=(10,6))
ax[0].plot(weeks, inf[0,:]/1000)
ax[0].set_xticks(yr)
ax[0].set_xticklabels(year_strings)
ax[0].set_ylabel("Inflow (BG)")
ax[0].set_title("Inflow timeseries from 2020-2065")

ax[1].plot(weeks, demand[0,52:]/1000)
ax[1].set_xticks(yr)
ax[1].set_xticklabels(year_strings)
ax[1].set_ylabel("Demand (BG)")
ax[1].set_title("Demand timeseries from 2020-2065")

ax[2].plot(weeks, storage_arr[0,:]/1000)
ax[2].set_xlabel("Years")
ax[2].set_xticks(yr)
ax[2].set_xticklabels(year_strings)
ax[2].set_ylabel("Storage (BG)")
ax[2].set_title("Storage timeseries from 2020-2065")

plt.tight_layout()
plt.savefig("Figures/hydrology_r0.jpg")
plt.show()
