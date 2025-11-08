# first, load the dataset we use
# German Credit Dataset Loader
# First install the required package: pip install ucimlrepo

from ucimlrepo import fetch_ucirepo 
  
# fetch dataset 
statlog_german_credit_data = fetch_ucirepo(id=144) 
  
# data (as pandas dataframes) 
X = statlog_german_credit_data.data.features 
y = statlog_german_credit_data.data.targets 

# Save features and targets to CSV files
X.to_csv('data/german_credit_features.csv', index=False)
y.to_csv('data/german_credit_targets.csv', index=False)
  
# # metadata 
# print(statlog_german_credit_data.metadata) 
  
# # variable information 
# print(statlog_german_credit_data.variables)
