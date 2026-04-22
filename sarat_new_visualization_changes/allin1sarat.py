# -*- coding: utf-8 -*-
"""
Created on Sun Jan 25 18:48:19 2026

@author: Arka
"""

import os

import sarat_visuals

def run_sarat_analysis(id_number,input_path,num_trajectories=500, interval_size=24, plot_sighted_positions=True,beacontrack=False):
    """
    One-line execution for the SARAT visualization pipeline.
    Returns all data needed for plotting.
    """

    
    # 0. Automatically generate filenames using the ID
    currentfile = os.path.join(input_path, f"current{id_number}.nc")
    drifterfile = os.path.join(input_path, f"drifter{id_number}.txt")
    completetraj    = os.path.join(input_path, f"complete_traj_{id_number}.dat")
    containerspath=os.path.join(input_path, "containers_sighted_locations.txt")

    print(f"--- Starting Analysis for ID: {id_number} ---")
    
    trajectories,trajectory_length=sarat_visuals.traj_prop(completetraj,num_trajectories)

    sighted_positions = sarat_visuals.containerissue(plot_sighted_positions,containerspath)

    if beacontrack:
        beacon_lon, beacon_lat, beacon_time = sarat_visuals.get_drifter_track(currentfile, drifterfile)

    # NetCDF file not available locally - set to None for now
    # current_ds,start_time, end_time, time_length ,ds_hourly=sarat_visuals.currentncproc(currentfile)
    current_ds = None
    start_time = None
    end_time = None
    time_length = None
    ds_hourly = None


    trajectories, grid_meta=sarat_visuals.setup_scientific_grid(trajectories, grid_size=0.1, padding=0.15)

    intervals=sarat_visuals.interval(interval_size,trajectory_length)


    centroids,max_prob_global,probs,prob_grids=sarat_visuals.prob_centroid(grid_meta,intervals,trajectories)

    # Return a dictionary of everything so you can access results easily
    # return trajectories,trajectory_length,sighted_positions,beacon_lon,beacon_lat,beacon_time,\
    #     current_ds,start_time,end_time,time_length,ds_hourlyhome/arkaprava/INCOIS_ARO/SARAT_V3_Visualization/pyfunc/,trajectories,grid_meta,\
    #         centroids,max_prob_global,probs,prob_grids
    if beacontrack:
        return {
            "trajectories": trajectories,
            "trajectory_length":trajectory_length,
            "sighted_positions":sighted_positions,
            "beacon_lon":beacon_lon,
            "beacon_lat":beacon_lat,
            "beacon_time":beacon_time,
            "current_ds":current_ds,
            "start_time":start_time,
            "end_time":end_time,
            "time_length":time_length,
            "ds_hourly":ds_hourly,
            "grid_meta":grid_meta,
            "centroids":centroids,
            "max_prob_global":max_prob_global,
            "probs":probs,
            "prob_grids":prob_grids,
            "intervals":intervals
            }
    else:
        return {
            "trajectories": trajectories,
            "trajectory_length":trajectory_length,
            "sighted_positions":sighted_positions,
            # "beacon_lon":beacon_lon,
            # "beacon_lat":beacon_lat,
            # "beacon_time":beacon_time,
            "current_ds":current_ds,
            "start_time":start_time,
            "end_time":end_time,
            "time_length":time_length,
            "ds_hourly":ds_hourly,
            "grid_meta":grid_meta,
            "centroids":centroids,
            "max_prob_global":max_prob_global,
            "probs":probs,
            "prob_grids":prob_grids,
            "intervals":intervals
            }
    
        


