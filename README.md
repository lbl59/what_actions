# SINGLE-UTILITY SINGLE-ACTION
We choose Cary as our actor (utility) for this test case.

## Characteristics of Cary
Total reservoir capacity: 14.9 bil gal\
Receives all of its supply from Jordan Lake (35.5% of total supply allocation)\
The only utility that operates a water treatment plant on the Jordan Lake

## Assumptions
1. Cary is the only actor in this system
2. Only Jordan Lake evaporation and inflows are significant to Cary
3. Cary receives 35.5% of the Jordan Lake inflows
4. No infrastructure will be triggered throughout the 26 years of simulation
5. No spillage
6. Failure criteria: reservoir storage (Jordan Lake) drops below 20% of capacity for 
   at least one week in a given year
7. Action: Trigger water restriction if system failure occurs

## Units
Demands: million gallons/week\
Inflows: million gallons/week\
Evaporation rate: million gallons/week\
Storage: billion gallons

## Data files
1. cary_demand.csv: 250 realizations of 26 years of projected future demands
2. jordan_lake_evap.csv: 250 realizations of 98 years of synthetic stationary evaporation rates for Jordan Lake
3. jordan_lake_inflow.csv: 250 realizations of 98 years of synthetic stationary inflows to Jordan Lake

## Code files
1. rof_table_generator.py
   - generates a folder containing the ROF tables for the desired number of realizations
   - ROF tables (csv files) found in the rof_tables folder
   - the rows are the reservoir storage level (0%, 5%,...100%)
   - the columns are the ROF for a week in the demand timeseries
   - 10 realizations takes ~34 minutes
2. tradeoff.py: 
   - conducts ROF evaluation on the synthetic demand, inflow and evaporation rates
   - visualizes the tradeoff between reliability and restriction frequency

## REFERENCES
Gold et al 2019, Identifying Actionable Compromises: Navigating Multi-City Robustness
Conflicts to Discover Cooperative Safe Operativng Spaces for Regional Water Supply
Portfolios

Trindade et al 2019, Deeply uncertain pathways: Integrated multi-city regional water 
supply infrastructure investment and portfolio management

Zeff et al 2014, Cooperative drought adaptation: Intergrating infrastructure development,
conservation, and water transfers into adaptive policy pathways


