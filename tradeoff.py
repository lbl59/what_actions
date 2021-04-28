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
evap = 2*np.loadtxt(evap_file, delimiter=",")
inflows = 0.05*np.loadtxt(inflow_file, delimiter=",")
demand = 1.1*np.loadtxt(demand_file, delimiter=",")

# Fixed values ######################################################
reservoir_capacity = 14900*0.127
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary"
n_sym_years = int(demand.shape[1] / n_weeks)
n_sym_weeks = int(demand.shape[1])

# Helper functions ##################################################

# Checks if the current storage is lower than 20% of full capacity
# @param st_next The storage at the next timestep
# @retuns 1 if failure is detected, 0 otherwise
def check_failure(st_next):
    if (st_next/reservoir_capacity) < 0.2:
        return 1
    else:
        return 0

# Evaluates ROF for the demand timeseries of realization
# @returns the predicted ROFs for this realization
def rof_evaluation(s_0, demand, inflows, evap, r):
    # rof timeseries for realization r
    rof_r = np.zeros(n_sym_weeks-n_weeks, dtype=float)

    demand_r = demand[r,:]
    for w in range(52, n_sym_weeks):
        # inflow and evaporation rate start time
        end_point = inflows.shape[1] - demand.shape[1] + w
        start_point = end_point - (n_hist_years*n_weeks)

        evap_r = evap[r, start_point:end_point]
        inflows_r = inflows[r, start_point:end_point]
        fail_count = 0

        demand_year = demand_r[w-n_weeks:w]
        # for this demand timeseries (vector) and initial storage (const)
        # obtain the probability of failure over 50 years of
        # historical inflow and evaporation rates
        for n in range(n_hist_years):
            # evap_year and inflow_year should have length 52
            evap_year = evap_r[n*n_weeks : (n+1)*n_weeks]
            inflow_year = inflows_r[n*n_weeks :  (n+1)*n_weeks]
            s_t = s_0
            count = 0
            for d in range(len(demand_year)):
                s_tnext = s_t - evap_year[d] + inflow_year[d] - demand_year[d]
                if (check_failure(s_tnext) == 1):
                    count += 1
                s_t = s_tnext
            if count > 0:
                fail_count += 1
        rof_r[w-52] = fail_count / n_hist_years
    return rof_r

# Evaluates if any of the weekly ROFs in the current  realization exceed alpha
# If true, trigger a restriction, else do nothing
# @returns an array of 1 or 0 depending on if restrictions are triggered
def restriction_check(rof_r, alpha):
    restriction = np.zeros(len(rof_r), dtype=float)
    for i in range(len(rof_r)):
        if rof_r[i] >= alpha:
            restriction[i] = 1
    return restriction

def storage_r(s_0, demand, inflows, evap, r, alpha):
    rof_r = rof_evaluation(s_0, demand, inflows, evap, r)
    print("ROF = ", rof_r)
    restriction = restriction_check(rof_r, alpha)
    rf = 0 # restriction frequency
    sp = inflows.shape[1] - demand.shape[1] + n_weeks

    demand_r = demand[r, n_weeks:]
    inflow_r = inflows[r, sp:]
    evap_r = evap[r, sp:]
    storage_r = np.zeros(len(demand_r), dtype=float)

    storage_r[0] = s_0
    i = 1
    while i < len(demand_r):
        # during water restrictions, only 90% of demand is met
        if restriction[i-1] == 1:
            rf += 1
            mth = np.min([4, len(demand_r)-i])
            for m in range(mth):
                storage_r[i] = storage_r[i-1] - evap_r[i-1] + inflow_r[i-1] - (0.9*demand_r[i-1])
                i += 1
        else:
            storage_r[i] = storage_r[i-1] - evap_r[i-1] + inflow_r[i-1] - demand_r[i-1]
            i += 1

    return rf, storage_r

# check reliability and avg restriction frequency for a given alpha
def reliability_rf_check(s_0, demand, inflows, evap, N_reals, alpha):
    failure = 0
    rf_tot = 0
    for r in range(N_reals):
        rf_r, st_r = storage_r(s_0, demand, inflows, evap, r, alpha)
        print(st_r)
        rf_tot += rf_r
        if (np.any(st_r) < (0.2*reservoir_capacity)):
            failure += 1
    rel = 1.0 - (failure/N_reals*n_sym_years)
    rf_avg = rf_tot/(N_reals*n_sym_years)
    return rel, rf_avg

# to modify ##########################################################
N_reals = 10  # number of realizations
s_0 = reservoir_capacity*0.4    # set an arbitrary starting storage level
n_hist_years = 50
# tradeoff between reliability and restriction frequency
alpha_vec = np.arange(0.00,1.05, 0.05)

reliability = np.zeros(len(alpha_vec), dtype=float)
restr_freq = np.zeros(len(alpha_vec), dtype=float)

for i in range(len(alpha_vec)):
    print("alpha = ", alpha_vec[i])
    a = alpha_vec[i]
    rel, rf_avg = reliability_rf_check(s_0, demand, inflows, evap, N_reals, a)
    reliability[i] = rel
    restr_freq[i] = rf_avg

print("Reliability = ", reliability)
print("Restrictions = ", restr_freq)
np.savetxt("reliability.csv", reliability)
np.savetxt("restriction_freq.csv", restr_freq)

plt.scatter(restr_freq, reliability, c=alpha_vec, cmap="YlOrBr")
plt.ylabel(r'Max reliability $\rightarrow$')
plt.xlabel(r'$\leftarrow$ Min restriction frequency')
plt.ylim([0.98, 1.0])
plt.title('Reliability vs restriction frequency')
cbar = plt.colorbar()
cbar.set_label(r'ROF trigger $\alpha$')
plt.savefig("RF_vs_Rel.png")
plt.show()
