# Postprocess

# Missing from hotels Bohinj: 01/07/2019 - 01/08-2019 - No hotels avaialable

import pandas as pd

def hf_to_csv(hf_filename, csv_filename):
    
    with pd.HDFStore(hf_filename) as hdf:
            keys = hdf.keys()
    
    dfs = []
    
    for key in keys:
        df = pd.read_hdf(hf_filename, key = key)
        dfs.append(df)
        
    df = pd.concat(dfs, ignore_index = True)
    
    df.to_csv(csv_filename, index = False, sep = '\t')
    
    return


if __name__ == "__main__":
    
    hf_to_csv('hotel_data.h5', 'hotels.csv')
    hf_to_csv('flight_data.h5', 'flights.csv')