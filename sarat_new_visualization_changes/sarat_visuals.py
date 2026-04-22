#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 17:03:08 2026

@author: arkaprava
"""

###################this section is to read the trajectory file where the completetraj is the 
#complete_traj_{id_number}.dat file and the num_trajectories is usually considered as 500
##
import pandas as pd

def traj_prop(completetraj,num_trajectories):
    data = pd.read_csv(completetraj, sep='\s+', header=None).values
    #data contains all the longitude and latitude values of all the resulted trajectories within 
    #simulation time

    trajectory_length = data.shape[0] // num_trajectories  # Calculate trajectory length from data

###where trajectory length refers to the time range in hours
    if data.shape[0] % trajectory_length != 0:
        raise ValueError("Data length is not divisible by trajectory length.")

    trajectories = data.reshape((num_trajectories, -1, 2))
    #reshaping the actual data in (numberoftrajectory*days*[lon*lat])
    return trajectories,trajectory_length
######it returens the trajectories of each timestep with their coordinates

# %% container
################################   not required for operational purpose#  ###########################
import numpy as np


def containerissue(plot_sighted_positions,file_path="containers_sighted_locations.txt"):
    if plot_sighted_positions:
        try:
            sighted_data = np.loadtxt(file_path, usecols=(0, 1))  # Assuming columns are longitude, latitude
            return sighted_data
        except FileNotFoundError:
            print(f"Warning: {file_path} not found. No sighted positions will be plotted.")
            return None
    return None

# Now, when you call it, you tell it whether to plot or not:
# %% drifter issue
################################   not required for operational purpose#  ###########################


import datetime as dt
import xarray as xr

def get_drifter_track(current_nc_path, drifter_txt_path):
# 1. Load the file using whitespace separator to catch all columns
    df = pd.read_csv(drifter_txt_path, sep='\s+', header=None)

    # 2. Check structure: How many columns are there?
    # If it's the new format (Year Month Day Hour Lon Lat ...), it will have > 5 columns    
    if df.shape[1] > 6: 
        df = df.iloc[:, [0, 1, 2, 3, 6, 7]]
        print(f"Detected Date-Separated format for {drifter_txt_path}")
        # Assuming format: Year(0) Month(1) Day(2) Hour(3) Lon(4) Lat(5)
        if df.iloc[0, 4]>= 50 and df.iloc[0, 4]<= 100:
            df.columns = ['year', 'month', 'day', 'hour', 'lon', 'lat']
        else:
            df.columns = ['year', 'month', 'day', 'hour', 'lat', 'lon']

        # Combine into a real datetime object
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
        df = df[['time', 'lon', 'lat']]
        # def matlab_to_py_date(matlab_datenum):
        #     return (dt.datetime.fromordinal(int(matlab_datenum)) + 
        #             dt.timedelta(days=matlab_datenum % 1) - 
        #             dt.timedelta(days=366))

        # df['time'] = df['time'].apply(matlab_to_py_date)
        # df = df[['time', 'lon', 'lat']]

    else:
        print(f"Detected Matlab-Datenum format for {drifter_txt_path}")
        # Assuming original format: Datenum(0) Lon(1) Lat(2)
        df = df.iloc[:, :3]
        if df.iloc[0, 2]>= 50 and df.iloc[0, 2]<= 100:
            df.columns = ['time_raw', 'lat', 'lon']
        else:
            df.columns = ['time_raw', 'lon', 'lat']
        
        
        
        def matlab_to_py_date(matlab_datenum):
            return (dt.datetime.fromordinal(int(matlab_datenum)) + 
                    dt.timedelta(days=matlab_datenum % 1) - 
                    dt.timedelta(days=366))

        df['time'] = df['time_raw'].apply(matlab_to_py_date)
        df = df[['time', 'lon', 'lat']]
        

    # 3. Convert to Xarray
    # We use drop_duplicates to ensure the index is clean for xarray conversion
    ds = df.drop_duplicates('time').set_index('time').to_xarray()

    # 4. Open Current Data and Slice
    cur = xr.open_dataset(current_nc_path)
    
    # Slice drifter data to match the current file's start and end time
    dsc = ds.sel(time=slice(cur.time[0], cur.time[-1]))

    # 5. Extract Coordinates
    # .values returns the raw numpy arrays for easy handling
    beacon_lon = dsc.lon.values
    beacon_lat = dsc.lat.values
    beacon_time = dsc.time.values

    return beacon_lon, beacon_lat, beacon_time




# %%=== LOAD AND PROCESS OCEAN CURRENT DATA ===
def currentncproc(currentfile):#for averaging purpose it may need ,start_idx,end_idx
    current_ds = xr.open_dataset(currentfile) ####open the currentfile which should be the exttracted current file as 'current{id_number}.nc'
    time = current_ds['TAXNEW'].values #read the time variable
    start_time = pd.Timestamp(time[0]) ###read the start date
    end_time = pd.Timestamp(time[-1]) ####read the end date
    ds_hourly = current_ds.resample(TAXNEW='1h').interpolate('linear') #convert the 3hourly data into hourly so that we can average accordingly
    # max_time_idx = current_ds.sizes['time']
    # if start_idx >= max_time_idx:
    #     print(f"Warning: Start index {start_idx} exceeds available time steps ({max_time_idx}). No current data available.")
    #     return None
    # end_idx = min(end_idx, max_time_idx)
    # currentavg=current_ds.isel(time=slice(start_idx, end_idx)).mean(dim='time')

    
    return current_ds,start_time, end_time, len(time),ds_hourly
###provides the actual current data, start date, end_date, length of time and converted hourly data

# %%


def setup_scientific_grid(trajectories, grid_size=0.1, padding=0.15):
    """
    Cleans trajectories by masking stationary starting points and 
    calculates a static geographic grid for probability mapping.
    """
    # 1. CLEANING: Mask points that haven't moved from their origin
    # We keep the first point [:, 0:1, :] but mask subsequent identical points
    first_points = trajectories[:, 0:1, :] ######calculate the first coordinate of each trajectories
    mask = np.all(np.isclose(trajectories[:, 1:, :], first_points), axis=-1)
    #creates a mask to know if any cooordinates match with the starting point, which means they are stuck 
    # Apply the mask to set "stuck" points to NaN
    trajectories[:, 1:, 0][mask] = np.nan
    trajectories[:, 1:, 1][mask] = np.nan
    
    ####this line can be removed 

    # 2. BOUNDARY DETECTION: Ignore NaNs to find the data envelope
    valid_lon = trajectories[:, :, 0][~np.isnan(trajectories[:, :, 0])]
    valid_lat = trajectories[:, :, 1][~np.isnan(trajectories[:, :, 1])]
###extract out all the nonnan values if the size is zero it will show the following error
    if valid_lon.size == 0 or valid_lat.size == 0:
        raise ValueError("No valid trajectory data found to create a grid.")

    # Define raw limits
    #Find the minimum and maximum values of longitude and latitude from the valid points found previously
    #then either rounds down or rounds up to define the box 
    min_lon, max_lon = np.floor(valid_lon.min()), np.ceil(valid_lon.max())
    min_lat, max_lat = np.floor(valid_lat.min()), np.ceil(valid_lat.max())

    # 3. PADDING: Expand the box by 15% (or your chosen padding)
    ##to keep a certain buffer zone so that map has enough space to show things in a cleaner way
    lon_pad = (max_lon - min_lon) * padding
    lat_pad = (max_lat - min_lat) * padding

#######extend the minimum and maximum values of longitude and latitude 
    min_lon -= lon_pad
    max_lon += lon_pad
    min_lat -= lat_pad
    max_lat += lat_pad

    # 4. GRID GENERATION: Create bins and ticks
    lon_bins = np.arange(min_lon, max_lon + grid_size, grid_size)
    lat_bins = np.arange(min_lat, max_lat + grid_size, grid_size)
    



    # Ticks for every 1 degree (standard for regional ocean maps)
    lon_ticks = np.arange(np.ceil(min_lon), np.floor(max_lon) + 1)
    lat_ticks = np.arange(np.ceil(min_lat), np.floor(max_lat) + 1)

    # Dictionary is a clean way to return many related variables
    grid_meta = {
        "lon_bins": lon_bins,
        "lat_bins": lat_bins,
        "lon_ticks": lon_ticks,
        "lat_ticks": lat_ticks,
        "n_lon_bins": len(lon_bins) - 1,
        "n_lat_bins": len(lat_bins) - 1,
        "extent": [min_lon, max_lon, min_lat, max_lat]
    }

    return trajectories, grid_meta #it stores all the variables into a dictonary referred as grid_meta to make the function and code cleaaner
# %%

##interval size will be a manual input, in general it is taken as daily so 24 is considered as the output is hourly
#it creates interval based on intervalsize and the length of trajectories 

def interval(interval_size,trajectory_length):
    intervals = [(i, i + interval_size) for i in range(0, trajectory_length, interval_size)
                 if i + interval_size <= trajectory_length]# if the length is 75 and intervalsize is 24, 
    if intervals and intervals[-1][1] < trajectory_length:
        intervals.append((intervals[-1][1], trajectory_length))#it creates [0 24,24 48,48 72,72 75]
    return intervals
# %% prob and centroid
def prob_centroid(grid_meta,intervals,trajectories):
    prob_grids = [] ###initiate two variables, which will be used later
    max_prob_global = 0##initation
    for start, end in intervals:
        # Flatten all active lon/lat points into two long arrays
        current_data = trajectories[:, start:end, :].reshape(-1, 2)#extract the trajectories coming in that interval
        valid = current_data[~np.isnan(current_data[:, 0])]#remove the nan values
        
        


        # 2. Initialize every grid point with an equal baseline (e.g., 1)
        # This represents your "Prior" probability
        # Count everything at once
        counts, _, _ = np.histogram2d(valid[:, 1], valid[:, 0], bins=[grid_meta['lat_bins'], grid_meta['lon_bins']])
        #calculate the total numbers of coordinates of the lat_bins and lon_bins 
        #for how many times they appear from each trajectory 
        
        # Convert to percentage
        probs = (counts / counts.sum()) * 100 if counts.sum() > 0 else counts
        prob_grids.append(probs)#it will change the variable accordingly, which was inititated earlier
        max_prob_global = max(max_prob_global, np.max(probs))#update the maximum value of the probability
        centroids = np.nanmean(trajectories, axis=0)# calculate the centroids which will further divided according to the interval in which they will be plotted
        
        return centroids,max_prob_global,probs,prob_grids
        

    
# %%=== CALCULATE CENTROIDS FOR ALL TIME STEPS ===


def plot_individual(output_path,intervals, trajectories, centroids, ds_hourly, 
                             lon_bins, lat_bins,
                             max_prob_global,beacon_time=None, beacon_lon=None,
                             beacon_lat=None, xlow=None,xhigh=None,ylow=None,yhigh=None, 
                             sighted_positions=None, plot_beacon_track=True,plot_individual=True,
                             xylimit=True,plot_sighted_positions=True,
                             reference_vector_length = 0.5, 
                             output_prefix="seeding"):
    """
    Creates individual PNG maps for each time interval.
    """
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import get_cmap
    from matplotlib.patches import Rectangle
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import numpy as np
    import os
    
    # Extents for the map, give the limit either manually or based on the maximum values
    if xylimit:
        min_lon,max_lon=xlow,xhigh
        min_lat,max_lat=ylow,yhigh
    else:    
        min_lon, max_lon = lon_bins[0], lon_bins[-1]
        min_lat, max_lat = lat_bins[0], lat_bins[-1]
    
    lon_ticks = np.arange(np.ceil(min_lon), np.floor(max_lon) + 1)
    lat_ticks = np.arange(np.ceil(min_lat), np.floor(max_lat) + 1)
    
    cmap = get_cmap("PuBuGn")#fixing the colormap

    if plot_individual:
        for idx, (start, end) in enumerate(intervals):
            # 1. Setup Figure and the surrounding land
            fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            ax.add_feature(cfeature.LAND, facecolor='lightgray')
            ax.coastlines(linewidth=0.5)

            # 2. Real Drifter Track
            if plot_beacon_track:
                dt_end = beacon_time[min(end, len(beacon_time)-1)]
                m = beacon_time <= dt_end
                ax.plot(beacon_lon[m], beacon_lat[m], 'magenta', lw=1.5, label='final drifter')

            # 3. Probability Grid (Fast Version)
            step_data = trajectories[:, start:end, :].reshape(-1, 2)
            valid_pts = step_data[~np.isnan(step_data[:, 0])]
            
            if len(valid_pts) == 0: # Handle "No Data" intervals
                with open("bounding_rect_and_centroid.txt", "a") as f:
                    f.write(f"{start}-{end},0.0,0.0,0.0,0.0,0.0,0.0\n")
                plt.savefig(f"seeding_{start}_{end}.png"); plt.close(); continue

            counts, _, _ = np.histogram2d(valid_pts[:, 1], valid_pts[:, 0], bins=[lat_bins, lon_bins])#change the tcounts name with counts
            # n_lat = len(lat_bins) - 1####remove
            # n_lon = len(lon_bins) - 1##remove
            # prior_counts = np.ones((n_lat, n_lon))######remove
            # counts=prior_counts+tcounts   ####line should be removed


            probs = (counts / counts.sum()) * 100
            im = ax.imshow(np.ma.masked_where(counts == 0, probs), origin="lower", cmap=cmap,
                           extent=[lon_bins[0], lon_bins[-1], lat_bins[0], lat_bins[-1]],
                           norm=Normalize(0, max_prob_global), transform=ccrs.PlateCarree())

            # 4. Currents (Quiver)
            currentavg=ds_hourly.isel(TAXNEW=slice(start, end)).mean(dim='TAXNEW')
            u_name = list(currentavg.data_vars)[0] 
            v_name = list(currentavg.data_vars)[1]
            
            u_data=currentavg[u_name]
            v_data=currentavg[v_name]

    # Now access them dynamically if there is depth in the current file, which should usually not be there
            if u_data.ndim == 3 and u_data.shape[0]<10:
                u_data = u_data.squeeze(dim='DEPTH1_1')
                v_data = v_data.squeeze(dim='DEPTH1_1')
            
            
            if currentavg is not None and u_data.shape[1]==v_data.shape[1]:
                q=ax.quiver(u_data.LON[::5], u_data.LAT[::5], u_data[::5,::5], v_data[::5,::5], scale=10)
                ax.quiverkey(q, 0.1, 0.95, reference_vector_length, f'{reference_vector_length} m/s', labelpos='E')
            else:
                q = ax.quiver(u_data.LON[::5], u_data.LAT[::5], u_data[::5,::5], v_data[::5, :-1:5], scale=10)
                ax.quiverkey(q, 0.1, 0.95, reference_vector_length, f'{reference_vector_length} m/s', labelpos='E')
            
            if start < len(centroids) and not np.any(np.isnan(centroids[start])):
                ax.plot(centroids[start][0], centroids[start][1], 'o', markersize=6, markeredgecolor='black', fillstyle='none', label='Interval Centroids', transform=ccrs.PlateCarree())
            if not np.any(np.isnan(centroids[end - 1])):
                if start == 0 or np.any(np.isnan(centroids[start])):
                    ax.plot(centroids[end - 1][0], centroids[end - 1][1], 'o', markersize=6, markeredgecolor='black', fillstyle='none', transform=ccrs.PlateCarree())
                else:
                    ax.plot(centroids[end - 1][0], centroids[end - 1][1], 'o', markersize=6, markeredgecolor='black', fillstyle='none', transform=ccrs.PlateCarree())
           
            # 5. Bounding Box & File Export
            pos = np.argwhere(counts > 0)
            y_min, x_min = pos.min(axis=0); y_max, x_max = pos.max(axis=0)
            rx, ry = lon_bins[x_min], lat_bins[y_min]
            rw, rh = lon_bins[x_max+1] - rx, lat_bins[y_max+1] - ry
            ax.add_patch(Rectangle((rx, ry), rw, rh, fill=False, edgecolor='blue', ls='--'))
            
            
            
            c_lon, c_lat = centroids[end-1]
            with open("bounding_rect_and_centroid.txt", "a") as f:
                f.write(f"{start}-{end},{rx:.4f},{ry:.4f},{rx+rw:.4f},{ry+rh:.4f},{c_lon:.4f},{c_lat:.4f}\n")

            # 6. Formatting & Save
            ax.plot(centroids[:end, 0], centroids[:end, 1], 'g-', label='Centroid Track')
            ax.plot(np.nanmean(trajectories[:,0,0]), np.nanmean(trajectories[:,0,1]), 'r*', ms=12)
            
            # for city in visible_cities:
            #     ax.plot(city["lon"], city["lat"], 'po', ms=5)
            #     ax.text(city["lon"], city["lat"], city["name"], fontsize=6)
            #to plot if any information was there for sighted things 
            if plot_sighted_positions and sighted_positions is not None:
                ax.plot(sighted_positions[:, 0], sighted_positions[:, 1], marker='^', color='brown', markersize=8, linestyle='None', label='Sighted Containers', transform=ccrs.PlateCarree())

#fixing the final things like extent, ticksm colorbar, legend title and saving the image
            ax.set_extent([min_lon, max_lon, min_lat, max_lat])
            ax.set_xticks(lon_ticks, crs=ccrs.PlateCarree())
            ax.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
            ax.legend(fontsize=6, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
            plt.colorbar(im, label="Probability (%)", pad=0.02, fraction=0.04)
            plt.title(f"Hours: {start}-{end}")
            filename = f"{output_prefix}_{start}_{end}.png"
            save_path = os.path.join(output_path, filename)
            plt.savefig(save_path)
            plt.close()
    
# %%


def plot_combined(output_path,id_number,intervals, trajectories, centroids, ds_hourly, 
                             lon_bins, lat_bins,max_prob_global,beacon_time=None, beacon_lon=None,
                             beacon_lat=None, xlow=None,xhigh=None,ylow=None,yhigh=None, 
                             sighted_positions=None,
                             plot_beacon_track=True,plot_combined=True,plot_sighted_positions=True,
                             xylimit=True,reference_vector_length = 0.5, 
                             output_prefix="seeding"):
    
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import get_cmap
    from matplotlib.patches import Rectangle
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import numpy as np
    import os
    
    if xylimit:
        min_lon,max_lon=xlow,xhigh
        min_lat,max_lat=ylow,yhigh
    else:    
        min_lon, max_lon = lon_bins[0], lon_bins[-1]
        min_lat, max_lat = lat_bins[0], lat_bins[-1]
    
    lon_ticks = np.arange(np.ceil(min_lon), np.floor(max_lon) + 1)
    lat_ticks = np.arange(np.ceil(min_lat), np.floor(max_lat) + 1)
    
    cmap = get_cmap("PuBuGn")
    if plot_combined:
        n = len(intervals)
        rows, cols = (n + 2) // 3, min(n, 3)####this line is only added to make all the figures together with the subplots
        fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 6*rows), 
                                 subplot_kw={'projection': ccrs.PlateCarree()})
        axes = np.array(axes).flatten()

        for idx, (start, end) in enumerate(intervals):
            ax = axes[idx]
            ax.add_feature(cfeature.LAND, facecolor='lightgray')
            ax.coastlines(lw=0.5)

            # 1. Faster Probability Calculation
            step_data = trajectories[:, start:end, :].reshape(-1, 2)
            valid_pts = step_data[~np.isnan(step_data[:, 0])]
            
            if len(valid_pts) > 0:
                counts, _, _ = np.histogram2d(valid_pts[:, 1], valid_pts[:, 0], bins=[lat_bins, lon_bins])#change the tcounts name with counts


                probs = (counts / counts.sum()) * 100
                im = ax.imshow(np.ma.masked_where(counts == 0, probs), origin="lower", cmap=cmap,
                               extent=[lon_bins[0], lon_bins[-1], lat_bins[0], lat_bins[-1]],
                               norm=Normalize(0, max_prob_global), transform=ccrs.PlateCarree())
                plt.colorbar(im, ax=ax, label="Prob (%)", pad=0.02, fraction=0.04)

                # 2. Bounding Box Logic
                pos = np.argwhere(counts > 0)
                y_min, x_min = pos.min(axis=0); y_max, x_max = pos.max(axis=0)
                rx, ry = lon_bins[x_min], lat_bins[y_min]
                rw, rh = lon_bins[x_max+1] - rx, lat_bins[y_max+1] - ry
                ax.add_patch(Rectangle((rx, ry), rw, rh, fill=False, edgecolor='blue', ls='--'))
                
                ##add the following lines if we need two boxes otherwise remove the part

                
                
            # 2. Real Drifter Track
            if plot_beacon_track:
                dt_end = beacon_time[min(end, len(beacon_time)-1)]
                m = beacon_time <= dt_end
                ax.plot(beacon_lon[m], beacon_lat[m], 'magenta', lw=1.5, label='final drifter')


            # 3. Currents & Centroids
            currentavg=ds_hourly.isel(TAXNEW=slice(start, end)).mean(dim='TAXNEW')
            u_name = list(currentavg.data_vars)[0] 
            v_name = list(currentavg.data_vars)[1]
            
            u_data=currentavg[u_name]
            v_data=currentavg[v_name]

    # Now access them dynamically
            if u_data.ndim == 3 and u_data.shape[0]<10:
                u_data = u_data.squeeze(dim='DEPTH1_1')
                v_data = v_data.squeeze(dim='DEPTH1_1')

            
            
            if currentavg is not None and u_data.shape[1]==v_data.shape[1]:
                q=ax.quiver(u_data.LON[::5], u_data.LAT[::5], u_data[::5,::5], v_data[::5,::5], scale=10)
                if idx == 0: ax.quiverkey(q, 0.1, 0.95, reference_vector_length, f'{reference_vector_length} m/s')
            else:
                q = ax.quiver(u_data.LON[::5], u_data.LAT[::5], u_data[::5,::5], v_data[::5, :-1:5], scale=10)
                if idx == 0: ax.quiverkey(q, 0.1, 0.95, reference_vector_length, f'{reference_vector_length} m/s')

            ax.plot(centroids[:end, 0], centroids[:end, 1], 'g-', lw=1, label='Centroid')
            ax.plot(np.nanmean(trajectories[:,0,0]), np.nanmean(trajectories[:,0,1]), 'r*', ms=10)
            if start < len(centroids) and not np.any(np.isnan(centroids[start])):
                ax.plot(centroids[start][0], centroids[start][1], 'o', markersize=6, markeredgecolor='black', fillstyle='none', label='Interval Centroids', transform=ccrs.PlateCarree())
            if not np.any(np.isnan(centroids[end - 1])):
                if start == 0 or np.any(np.isnan(centroids[start])):
                    ax.plot(centroids[end - 1][0], centroids[end - 1][1], 'o', markersize=6, markeredgecolor='black', fillstyle='none', transform=ccrs.PlateCarree())
                else:
                    ax.plot(centroids[end - 1][0], centroids[end - 1][1], 'o', markersize=6, markeredgecolor='black', fillstyle='none', transform=ccrs.PlateCarree())

            if plot_sighted_positions and sighted_positions is not None:
                ax.plot(sighted_positions[:, 0], sighted_positions[:, 1], marker='^', color='brown', markersize=8, linestyle='None', label='Sighted Containers', transform=ccrs.PlateCarree())

            # 4. Standard Formatting
            ax.set_title(f"{start}-{end} hrs", fontweight="bold")
            ax.set_extent([min_lon, max_lon, min_lat, max_lat])
            ax.set_xticks(lon_ticks, crs=ccrs.PlateCarree())
            ax.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
            if idx == 0: ax.legend(fontsize=6, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)

        # Hide unused subplots
        for i in range(n, len(axes)): axes[i].axis('off')
        
        plt.tight_layout()
        filename = f"seeding_duration_{id_number}_combined.png"
        save_path = os.path.join(output_path, filename)
        plt.savefig(save_path, dpi=300)
        plt.close()
            

    print(f"Finished plotting {len(intervals)} intervals.")

