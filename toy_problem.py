import numpy as np
import random 
import time

# Timer code thanks to https://realpython.com/python-timer/
start = time.perf_counter()

# Modify file names and locations depending on test case ###########
evap = np.loadtxt("C:/Users/lilli/Desktop/Training/Risk-of-Failure/water_balance_files/jordan_lake_evap.csv", delimiter=",")
inflows = 0.355*(np.loadtxt("C:/Users/lilli/Desktop/Training/Risk-of-Failure/water_balance_files/jordan_lake_inflows.csv", delimiter=","))
demand = np.loadtxt("C:/Users/lilli/Desktop/Training/Risk-of-Failure/water_balance_files/cary_demand.csv", delimiter=",")

# FIxed values ######################################################
reservoir_capacity = 14.9*(10**3)
n_weeks = 52
n_years = int(np.floor(demand.shape[1] / n_weeks))
utility = "Cary

# To modify #########################################################
N_reals = 10  # Number of timeseries to generate ROF tables for   
N_rofs = 50     # Number of ROF simulations

n_sym_years = int(demand.shape[1] / n_weeks)
n_hist_years = int(np.floor(evap.shape[1] / n_weeks))

# Helper functions ##################################################

# Checks if the current storage is lower than 20% of full capacity
# @param st_next The storage at the next timestep
# @retuns 1 if failure is detected, 0 otherwise

def check_failure(st_next):
    if(st_next / reservoir_capacity) < 0.2:
        return 1
    else:
        return 0

# Calculates next storage given values of storage, evaporation rates, 
# inflows and demands at current timestep
# @param s_t, e_t, i_t, d_t Storage, evaporation rate, inflow and demand at time t
# @returns Storage at time t+1

def calc_storage(s_t, e_t, i_t, d_t):
    return s_t + e_t + i_t - d_t

# Ensures that the folder to store the ROF tables exists
# If the folder does not yet exist, create one
# Code thanks to Julieanne Quinn (Assistant Professor, University of Virginia)
# @param path The name of the path to the folder in which the output ROF tables are to be stored 

def assure_path_exists(path):
    '''Creates directory if it doesn't exist'''
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)
                
assure_path_exists(os.getcwd() + '/rof_tables/')
path = "C:/Users/lilli/Desktop/Training/Risk-of-Failure/rof_tables/"

# Choosing indices of realizations to generate ROF tables for
idx_reals = np.array(random.sample(np.arange(0, evap.shape[0]).tolist(), N_reals))

# Choosing n-random historical years to use in the ROF simulations
hist_years = np.array(random.sample(np.arange(0, n_hist_years).tolist(), N_rofs))

tiers = np.arange(0.0, 1.05, 0.05)      # storage tiers from 0% to 100% in increments of 5%

for r in range(N_reals):

    # vectors of synthetic demands and historical evaporation and inflows
    demand_r = demand[idx_reals[r], :]  
    evap_r = evap[idx_reals[r], :]  
    inflow_r = inflows[idx_reals[r], :]  
    #print("Obtained demand, evaporation, inflow for realization ", r)
    
    rof_table_r = np.zeros((len(tiers), int(demand.shape[1]-n_weeks)), dtype=float)
    #print("Initialized ROF table for realization ", r)
    
    for t in range(len(tiers)):      
        storage_tier = tiers[t]*reservoir_capacity
           
        for d in range(0,len(demand_r)-n_weeks):
            demand_year = demand_r[d:d+52]
            fail_count = 0
            
            for n in range(len(hist_years)):
                # for each yearly demand series, choose a random historical yearly evaporation
                # and inflow series
                hist_year = hist_years[n]

                # evap_year and inflow_year should have length 52
                evap_year = evap_r[(hist_year*n_weeks) : (n_weeks*hist_year)+n_weeks]
                inflow_year = inflow_r[(hist_year*n_weeks) :  (n_weeks*hist_year)+n_weeks]
                
                s_t = storage_tier
                for w in range(len(demand_year)):
                    s_tnext = calc_storage(s_t, evap_year[w], inflow_year[w], demand_year[w])
                    if (check_failure(s_tnext) == 0):
                        s_t = s_tnext
                    else:
                        fail_count += check_failure(s_tnext)
                        break
            rof_table_r[t,d] = fail_count / N_rofs

    file_name = path + utility + "_rof_table_r" + str(r) + ".csv"
    print("realization = ", r, " completed")
    np.savetxt(file_name, rof_table_r, delimiter=",")

end = time.perf_counter()
print(f"Time = {end - start:0.4f} seconds")



                    





