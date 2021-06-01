import numpy as np
import random
import os
import time

# Timer code thanks to https://realpython.com/python-timer/
start = time.perf_counter()

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
reservoir_capacity = 14.9*(10**3)*0.5
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary"

# To modify #########################################################
N_sow = int(demand.shape[0])  # Number of states of the world
N_reals = 10  # Choose the n-first realizations for which to generate ROF tables
N_rofs = 50     # Number of ROF simulations

n_sym_weeks = int(demand.shape[1])
n_sym_years = int(demand.shape[1] / n_weeks)

# Helper functions ##################################################

# Checks if the current storage is lower than 20% of full capacity
# @param st_next The storage at the next timestep
# @retuns 1 if failure is detected, 0 otherwise

def check_failure(st_next):
    if (st_next/reservoir_capacity) < 0.2:
        return 1
    else:
        return 0

# Helper functions ##################################################
def calc_storage(s_t, e_t, i_t, d_t):
    s_tnext = s_t - e_t + i_t - d_t
    if (s_tnext/reservoir_capacity) >= 1.0:
        return reservoir_capacity
    elif s_tnext < 0:
        return 0.0
    else:
        return s_tnext

# Ensures that the folder to store the ROF tables exists
# If the folder does not yet exist, create one
# Code thanks to Julianne Quinn (Assistant Professor, University of Virginia)
# @param path The name of the path to the folder in which the output ROF tables are to be stored

def assure_path_exists(path):
    '''Creates directory if it doesn't exist'''
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

assure_path_exists(cwd + '/rof_tables/')
path = cwd + "/rof_tables/"

# Get the number of historical evaporation and inflows to base the projected
# storage-to-demand dynamic on
n_hist_years = N_rofs
n_hist_weeks =  (n_hist_years*n_weeks) + n_weeks

tiers = np.arange(0.0, 1.05, 0.05)      # storage tiers from 0% to 100% in increments of 5%

# vectors of 50-years' worth of historical inflow and evaporation
evap_timeseries = evap[0,:]
inflow_timeseries = inflows[0,:]

# Start generating ROF tables
for r in range(N_reals):
    demand_r = demand[r,:]
    rof_table_r = np.zeros((len(tiers), n_sym_weeks-52), dtype=float)

    for t in range(len(tiers)):
        storage_tier = tiers[t]*reservoir_capacity

        for w in range(n_weeks,len(demand_r)):
            fail_count = 0
            demand_year = demand_r[w-n_weeks:w]
            # for this demand timeseries (vector) and initial storage (const)
            # obtain the probability of failure over 50 years of
            # historical inflow and evaporation rates
            for n in range(n_hist_years):
                idx_start = n*n_weeks + (w-n_weeks)
                idx_end = (n+1)*n_weeks + (w-n_weeks)
                # evap_year and inflow_year should have length 52
                evap_year = evap_timeseries[idx_start : idx_end]
                inflow_year = inflow_timeseries[idx_start : idx_end]
                s_t = storage_tier
                for d in range(len(demand_year)):
                    s_tnext = calc_storage(s_t, evap_year[d], inflow_year[d], demand_year[d])
                    if (check_failure(s_tnext) == 0):
                        s_t = s_tnext
                    else:
                        fail_count += 1
                        break
            rof_table_r[t, w-n_weeks] = fail_count / n_hist_years

    file_name = path + utility + "_rof_table_r" + str(r) + ".csv"
    print("realization = ", r, " completed")
    np.savetxt(file_name, rof_table_r, delimiter=",")

end = time.perf_counter()
print(f"Time = {end - start:0.4f} seconds")
