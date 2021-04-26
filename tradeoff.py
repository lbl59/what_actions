import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

sns.set_theme()
# Get cwd code thanks to https://thispointer.com/python-how-to-get-the-current-working-directory/
# Modify filenames and locations depending on test case ############
cwd = os.getcwd()
evap_file = cwd + "\water_balance_files\jordan_lake_evap.csv"
inflow_file = cwd + "\water_balance_files\jordan_lake_inflows.csv"
demand_file = cwd + "\water_balance_files\cary_demand.csv"

# Load .csv files  ##################################################
evap = np.loadtxt(evap_file, delimiter=",")
inflows = np.loadtxt(inflow_file, delimiter=",")
demand = np.loadtxt(demand_file, delimiter=",")

rof_tables = []
for each_file in glob.glob('C:/Users/lilli/Desktop/Training/Risk-of-Failure/rof_tables/*.csv'):
    rof_tables.append(each_file)

# Fixed values ######################################################
reservoir_capacity = 14.9*(10**3)
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary"
n_sym_years = int(demand.shape[1] / n_weeks)
n_sym_weeks = int(demand.shape[1])
# to modify ##########################################################
N_reals = 50  # number of realizations
s_0 = reservoir_capacity*0.40      # set an arbitrary starting storage level

# Helper functions ##################################################
# Calculates next storage given values of storage, evaporation rates,
# inflows and demands at current timestep
# @param s_t, e_t, i_t, d_t Storage, evaporation rate, inflow and demand at time t
# @returns Storage at time t+1
def calc_storage(s_t, e_t, i_t, d_t):
    return s_t + e_t + i_t - d_t

# Evaluates ROF for the demand timeseries of realization
# @returns the predicted ROFs for this realization
def rof_evaluation(s_0, demand, inflows, evap, r):
    # rof timeseries for realization r
    rof_r = np.zeros(n_sym_weeks-n_weeks)
    # inflow and evaporation rate start time
    sp = inflows.shape[1] - n_sym_weeks - 42
    for w in range(n_weeks, n_sym_weeks):
        fail_count = 0
        demand_year = demand[r, w-n_weeks:w]
        # for this demand timeseries (vector) and initial storage (const)
        # obtain the probability of failure over 50 years of
        # historical inflow and evaporation rates
        for n in range(n_hist_years):
            # evap_year and inflow_year should have length 52
            evap_year = evap_timeseries[(n*n_weeks)+sp : ((n+1)*n_weeks)+sp]
            inflow_year = inflow_timeseries[(n*n_weeks)+sp :  ((n+1)*n_weeks)+sp]
            s_t = s_0
            for d in range(len(demand_year)):
                s_tnext = calc_storage(s_t, evap_year[d], inflow_year[d], demand_year[d])
                if (check_failure(s_tnext) == 0):
                    s_t = s_tnext
                else:
                    fail_count += 1
                    break
        rof_r[w-n_weeks] = fail_count / n_hist_years

    return rof_r

# Evaluates if any of the weekly ROFs in the current  realization exceed alpha
# If true, trigger a restriction, else do nothing
# @returns an array of 1 or 0 depending on if restrictions are triggered
def restriction_check(rof_r, alpha):
    restriction = np.zeros(len(rof_r), dtype=int)
    for i in range(len(rof_r)):
        if rof_r[i] >= alpha:
            restriction[i] = 1
    return restriction

def storage_r(s_0, demand, inflows, evap, r, alpha):
    rof_r = rof_evaluation(s_0, demand, inflows, evap, r)
    restrictions = restriction_check(rof_r, alpha)
    starting_point = inflows.shape[1] - demand.shape[1] + 52

    demand_r = demand[r, 52:]
    inflow_r = inflows[r, starting_point:]
    evap_r = evap[r, starting_point:]
    storage_r = np.zeros(len(demand_r), dtype=float)

    storage_r[0] = s_0
    rf = 0      # restriction frequency
    for i in range(1, len(demand_r)):
        # during water restrictions, only 50% of demand is met
        if restriction[i] == 1:
            rf += 1
            storage_r[i] = calc_storage(storage_r[i-1], evap_r[i-1], inflow_r[i-1], 0.5*demand_r[i-1])
        else:
            storage_r[i] = calc_storage(storage_r[i-1], evap_r[i-1], inflow_r[i-1], demand_r[i-1])
    return rf, storage_r

# check reliability and avg restriction frequency for a given alpha
def reliability_rf_check(s_0, demand, inflows, evap, N_reals, alpha):
    reliability_fail = 0
    rf_tot = 0
    for r in range(N_reals):
        rf_r, st_r = storage_r(s_0, demand, inflows, evap, r, alpha)
        rf_tot += rf_r
        if (np.any(str_r) < 0.2*reservoir_capacity):
            reliability_fail += 1
    rel = reliability_fail/N_reals
    rf_avg = rf_tot/N_reals
    return rel, rf_avg

# tradeoff between reliability and restriction frequency
alpha_vec = np.arange(0,1.005, 0.05)
reliability = np.zeros(len(alpha_vec), dtype=float)
restr_freq = np.zeros(len(alpha_vec), dtype=float)
for i in range(len(alpha_vec)):
    a = alpha_vec[i]
    rel, rf_avg = reliability_rf_check(s_0, demand, inflows, evap, N_reals, a)
    reliability[i] = rel
    restr_freq[i] = rf_avg

fig, ax = plt.subplots()
ax.scatter(reliability, restr_freq, c=alpha_vec, cmap="YlOrBr")
ax.set_xlabel("Increasing reliability $\rightarrow$")
ax.set_ylabel("$\leftarrow$ Decreasing restriction frequency")
ax.set_title("Tradeoff between reliability and average restriction frequency \n 100 realizations")
cbar = plt.colorbar(ax, format=ticker.FuncFormatter(fmt))
cbar.set_label(r'ROF trigger $\alpha$')
plt.show()
