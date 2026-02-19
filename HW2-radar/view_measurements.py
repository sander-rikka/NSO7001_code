"""File to use in Spyder programm which enables to run sections separately."""
import pandas as pd
from matplotlib import pyplot as plt

#%%
#df = pd.read_csv('./data/tyri_meas_data_202410.csv')
df = pd.read_csv(r'data/tyri_meas_data_202410.csv')
df

#%%
df['Türi_PR1H'].plot()
plt.xticks(rotation=45)