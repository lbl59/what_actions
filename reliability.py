import numpy as np
import random 
import os
import glob
import time
from decimal import Decimal, ROUND_UP
import matplotlib.pyplot as plt

# Import all hydrologic files ######################################
# Modify file names and locations depending on test case ###########
evap = np.loadtxt("C:/Users/lilli/Desktop/Training/Risk-of-Failure/water_balance_files/jordan_lake_evap.csv", delimiter=",")
inflows = np.loadtxt("C:/Users/lilli/Desktop/Training/Risk-of-Failure/water_balance_files/jordan_lake_inflows.csv", delimiter=",")
demand = np.loadtxt("C:/Users/lilli/Desktop/Training/Risk-of-Failure/water_balance_files/cary_demand.csv", delimiter=",")
rof_tables = []
for each_file in glob.glob('C:/Users/lilli/Desktop/Training/Risk-of-Failure/rof_tables/*.csv'):
    rof_tables.append(each_file)

# Fixed values ######################################################
reservoir_capacity = 14.9*(10**3)
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary"
n_sym_years = int(demand.shape[1] / n_weeks)
n_hist_years = int(np.floor(evap.shape[1] / n_weeks))

# to modify ##########################################################
N_reals = len(rof_tables)      # number of realizations 
alpha = 0.05      # set an arbitrary ROF trigger value
s_t0 = reservoir_capacity*0.40      # set an arbitrary starting storage level

# choose N-random realizations to simulate storage on
# if N_reals = total number of realizations, 
# set idx_reals = np.arange(0,N_reals)
idx_reals = np.array(random.sample(np.arange(0, evap.shape[0]).tolist(), N_reals))

# Choosing n-random historical years to when simulating storage using
# historical inflow and evaporation with predicted demand
hist_years = np.array(random.sample(np.arange(0, n_hist_years - n_sym_years).tolist(), N_reals))

# Helper functions ##################################################

# Determines if the ROF for a given week of year in a given realization
# is higher than the pre-determined alpha
# @param rof_r The ROF table for a given realization r
# @param w A given week in the storage-demand timeseries in a given realization
# @param s_t Storage level for a given week in a given realization
# @param alpha The ROF trigger value
# @returns 1 if the ROF value > alpha, 0 otherwise
def trigger_restriction(rof_r, storage_r, alpha):
    for s in range(len(storage_r)):
        s_t = storage_r[s]
        frac_capacity = s_t / reservoir_capacity
        x = Decimal(str(frac_capacity))
        nearest_tier = (x*2).quantize(Decimal('.1'), rounding=ROUND_UP)/2
        tier_idx = np.where(rof_r[:,0] == nearest_tier)

        rof_rw = rof_r[tier_idx, s]
        if rof_rw > alpha:
            return 1
        else:
            continue
    return 0

# Calculates next storage given values of storage, evaporation rates, 
# inflows and demands at current timestep
# @param s_t, e_t, i_t, d_t Storage, evaporation rate, inflow and demand at time t
# @returns Storage at time t+1
def calc_storage(s_t, e_t, i_t, d_t):
    return s_t + e_t + i_t - d_t

def storage_r(demand, inflows, evap, hist_years, r):
    hist_start = hist_years[r]*n_weeks
    demand_r = demand[r,52:]
    inflow_r = inflows[r, hist_start:hist_start + len(demand_r)]
    evap_r = evap[r, hist_start:hist_start + len(demand_r)]
    storage_r = np.zeros(len(demand_r), dtype=float)
    storage_r[0] = s_t0
    for i in range(1, len(demand_r)):
        storage_r[i] = calc_storage(storage_r[i-1], evap_r[i-1], inflow_r[i-1], demand_r[i-1])

    return storage_r

# check reliability
def reliability_check(N_reals, demand, inflows, evap, hist_years, alpha):
    trigger_count = 0
    for r in range(N_reals):
        rof_r = np.loadtxt(rof_tables[r], delimiter=",")
        curr_storage = storage_r(demand, inflows, evap, hist_years, r)
        check_failure = trigger_restriction(rof_r, curr_storage, alpha)
        if check_failure == 1:
            trigger_count += 1
            break
        else:
            continue

    percent_fail = trigger_count / N_reals
    return percent_fail
    '''
    if(percent_fail < 0.01):
        print("System fails", str((percent_fail) *100), "% of the time", "\nSystem is reliable.")
    else:
        print("System fails", str((percent_fail) *100), "% of the time", "\nSystem is not reliable.")
    '''

alpha_vec = np.arange(0,1.005, 0.05)
percent_fail_vec = np.zeros(len(alpha_vec), dtype=float)
for i in range(len(alpha_vec)):
    a = alpha_vec[i]
    print("Curr alpha = ", a)
    percent_fail_vec[i] = (reliability_check(N_reals, demand, inflows, evap, hist_years, a))*100

fig, ax = plt.subplot()
ax.plot(alpha_vec, percent_fail_vec)
ax.set_xlabel(r"$\alpha$")
ax.set_ylabel("$\leftarrow$ Increasing reliability")
ax.set_title(r"Reliability, $r = 99%$ no failure")
plt.show()






