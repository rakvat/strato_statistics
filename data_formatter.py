import os
import glob
import pandas as pd


frames = []
for filename in glob.glob('data/*.txt'):
    month = filename.split('/')[1].split('.')[0][0:7]
    df = pd.read_csv(filename, sep = '\s+', header = None, names = ['count', 'url'])
    df['month'] = month
    frames.append(df)

full_data = pd.concat(frames)
filename = 'data/all.csv'
full_data.to_csv(filename, index = False, columns = ['month', 'url', 'count'])
