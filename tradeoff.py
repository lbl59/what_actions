import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from decimal import Decimal, ROUND_UP

sns.set_theme()
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

# Fixed values ######################################################
reservoir_capacity = 14900*0.5
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary"
n_sym_years = int(demand.shape[1] / n_weeks)
n_sym_weeks = int(demand.shape[1])

# Get the ROF tables ################################################
rof_tables = []
for each_file in glob.glob('C:/Users/lilli/Desktop/Risk-of-Failure/rof_tables/*.csv'):
    rof_tables.append(each_file)

# Helper functions ##################################################
def calc_storage(s_t, e_t, i_t, d_t):
    s_tnext = s_t - e_t + i_t - d_t
    if (s_tnext/reservoir_capacity) >= 1.0:
        return reservoir_capacity
    elif s_tnext < 0:
        return 0.0
    else:
        return s_tnext

# Checks if the current storage is lower than 20% of full capacity
# @param st_next The storage at the next timestep
# @retuns 1 if failure is detected, 0 otherwise
def check_failure(st_next):
    if (st_next/reservoir_capacity) < 0.2:
        return 1
    else:
        return 0

# Evaluates if any of the weekly ROFs in the current realization exceed alpha
# If true, trigger a restriction, else do nothing
# @returns 1 or 0 depending on if restrictions are triggered
def trigger_restriction(rof_r, s_t, w, alpha):
    frac_capacity = s_t / reservoir_capacity
    x = Decimal(str(frac_capacity))
    nearest_tier = (x*2).quantize(Decimal('.1'), rounding=ROUND_UP)/2
    tier_idx = int(nearest_tier*rof_r.shape[0])-1
    rof_rw = rof_r[tier_idx, w]
    if rof_rw > alpha:
        return 1, rof_rw
    #else:
        #continue
    return 0, rof_rw

def storage(demand, inflows, evap, alpha, tier):
    sp = inflows.shape[1] - demand.shape[1] + n_weeks
    restr_freq = np.zeros((N_reals, demand.shape[1]-n_weeks), dtype=int)
    restr_demand = np.zeros((N_reals, demand.shape[1]-n_weeks), dtype=float)
    storage_dynamics = np.zeros((N_reals, demand.shape[1]-n_weeks), dtype=float)
    short_term_risk = np.zeros((N_reals, demand.shape[1]-n_weeks), dtype=float)
    for r in range(len(rof_tables)):
        rof_r = np.loadtxt(rof_tables[r], delimiter=",")
        demand_r = demand[r, n_weeks:]
        inflow_r = inflows[r, sp:]
        evap_r = evap[r, sp:]

        storage_r = np.zeros(len(demand_r), dtype=float)
        rf_r = np.zeros(len(demand_r), dtype=int)
        rd_r = np.zeros(len(demand_r), dtype=float)
        risk_r = np.zeros(len(demand_r), dtype=float)
        storage_r[0] = reservoir_capacity*tier
        #s_t = reservoir_capacity*tier
        w = 1
        while w < len(demand_r):
            restrict, rof_rw = trigger_restriction(rof_r, storage_r[w-1], w-1, alpha)
            risk_r[w-1] = rof_rw
            # during water restrictions, only 90% of demand is met
            if restrict == 1:
                mth = np.min([4, len(demand_r)-w])
                rf_r[w-1] = restrict
                for m in range(mth):
                    rd_r[w-1] = 0.8*demand_r[w-1]
                    storage_r[w] = calc_storage(storage_r[w-1], evap_r[w-1], inflow_r[w-1], (0.8*demand_r[w-1]))
                    risk_r[w] = trigger_restriction(rof_r, storage_r[w], w, alpha)[1]
                    w += 1
            else:
                rd_r[w-1] = demand_r[w-1]
                storage_r[w] = calc_storage(storage_r[w-1], evap_r[w-1], inflow_r[w-1], demand_r[w-1])
                risk_r[w] = trigger_restriction(rof_r, storage_r[w], w, alpha)[1]
                w += 1
        restr_freq[r,:] = rf_r
        restr_demand[r,:] = rd_r
        storage_dynamics[r,:] = storage_r
        short_term_risk[r,:] = risk_r

    rf_filename = cwd + "/dynamics/restr_freq/restr_freq_" + str(tier) + "_" + f"{alpha:.2f}" + ".csv"
    rd_filename = cwd + "/dynamics/restr_demand/restr_demand_" + str(tier) + "_" + f"{alpha:.2f}" +".csv"
    str_filename = cwd + "/dynamics/str_dynamics/str_dynamics_" + str(tier) + "_" + f"{alpha:.2f}" +".csv"
    risk_filename = cwd + "/dynamics/short_term_risk/risk_" + str(tier) + "_" + f"{alpha:.2f}" +".csv"

    np.savetxt(rf_filename, restr_freq, delimiter=",")
    np.savetxt(rd_filename, restr_demand, delimiter=",")
    np.savetxt(str_filename, storage_dynamics, delimiter=",")
    np.savetxt(risk_filename, short_term_risk, delimiter=",")
    return restr_freq, restr_demand, storage_dynamics

def reliability_check(st_r, reservoir_capacity):
    for i in range(len(st_r)):
        if st_r[i] < (0.2*reservoir_capacity):
            return 1
        else:
            continue
    return 0

# check reliability and avg restriction frequency for a given alpha
def reliability_rf_check(demand, inflows, evap, N_reals, alpha, tier):
    failure = 0
    rf_tot = 0

    restr_freq, restr_demand, storage_dynamics = storage(demand, inflows, evap, alpha, tier)
    for r in range(N_reals):
        rf_r = restr_freq[r,:]
        rd_r = restr_demand[r,:]
        st_r = storage_dynamics[r,:]
        rf_tot += np.sum(rf_r)
        failure += reliability_check(st_r, reservoir_capacity)
    rel = 1.0 - (failure/N_reals)
    rf_avg = rf_tot/(N_reals)
    return rel, rf_avg

# to modify ##########################################################
N_reals = 100  # number of realizations
tier = 1.0   # fraction of reservoir that is filled
n_hist_years = 50
# tradeoff between reliability and restriction frequency
alpha_vec = np.arange(0.00,0.21, 0.01)

reliability = np.zeros(len(alpha_vec), dtype=float)
restr_freq = np.zeros(len(alpha_vec), dtype=float)

for i in range(len(alpha_vec)):
    print("alpha = ", alpha_vec[i])
    a = alpha_vec[i]
    rel, rf_avg = reliability_rf_check(demand, inflows, evap, N_reals, a, tier)
    reliability[i] = rel
    restr_freq[i] = rf_avg

print("Reliability = ", reliability)
print("Restrictions = ", restr_freq)
np.savetxt("reliability.csv", reliability)
np.savetxt("restriction_freq.csv", restr_freq)

plt.scatter(restr_freq, reliability, c=alpha_vec, cmap="YlOrBr")
plt.ylabel(r'Max reliability $\rightarrow$')
plt.xlabel(r'$\leftarrow$ Min restriction frequency')
#plt.ylim([0.98, 1.0])
plt.title('Reliability vs restriction frequency')
cbar = plt.colorbar()
cbar.set_label(r'ROF trigger $\alpha$')
plt.savefig("RF_vs_Rel.png")
plt.show()
