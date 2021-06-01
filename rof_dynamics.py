import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
import pandas as pd

sns.set_theme()
sns.set_style("white")
# Get the ROF tables ################################################
rf_data = []
for each_file in glob.glob('C:/Users/lilli/Desktop/Risk-of-Failure/dynamics/restr_freq/restr_freq_*.csv'):
    rf_data.append(each_file)
# Get cwd code thanks to https://thispointer.com/python-how-to-get-the-current-working-directory/
# Modify filenames and locations depending on test case ############
cwd = os.getcwd()
rf_filename = cwd + "/dynamics/restr_freq/restr_freq_1.0_0.05.csv"
rof_filename = cwd + "/dynamics/short_term_risk/risk_1.0_0.05.csv"
restr_freq = np.loadtxt(rf_filename, delimiter = ",")
rof = np.loadtxt(rof_filename, delimiter=",")
years= np.arange(0,2340,1)
r = 0

alpha = np.arange(0.0, 0.21, 0.01)
rf_r = restr_freq[r,:]
rof_r = rof[r,:]*100

restriction_year = np.zeros(len(alpha), dtype=int)
for i in range(len(alpha)):
    rf_alpha = np.loadtxt(rf_data[i], delimiter=",")
    rf_alpha_r = rf_alpha[r,:]
    first_restriction = np.nonzero(rf_alpha_r)
    restriction_year[i] =years[first_restriction][0]

inflow_file = cwd + "\water_balance_files\jordan_lake_inflows.csv"
demand_file = cwd + "\water_balance_files\cary_demand.csv"

inflows = 0.20*np.loadtxt(inflow_file, delimiter=",")
demand = 1.1*np.loadtxt(demand_file, delimiter=",")
sp = inflows.shape[1] - demand.shape[1] + 52

fig, ax = plt.subplots(figsize=(8,4))
y_pos = np.arange(len(alpha))
weeks = np.arange(0,90,1)
week_ticks = np.arange(0,95,5)
week_labels = week_ticks.astype(str)
ax.barh(y_pos, restriction_year, align='center', color="plum", label="First restriction")
ax.set_yticks(np.arange(0,25,5))
ax.set_yticklabels(np.arange(0,25,5).astype(str))
ax.set_xlabel('Week of first restriction')
ax.set_ylabel(r"$\alpha$ (%)")
ax.set_title('First water restriction implementation')

ax2=ax.twinx()
ax2.plot(weeks, inflows[0,sp:sp+90], label="Inflow (BG)", linewidth=1.2)
ax2.set_ylabel("Inflow (BG)")

handles, labels = [(a + b) for a, b in zip(ax.get_legend_handles_labels(), ax2.get_legend_handles_labels())]
plt.legend(handles, labels, loc = "lower right", fontsize=12)
#plt.savefig("Figures/first_restriction_r0.png")
plt.show()
