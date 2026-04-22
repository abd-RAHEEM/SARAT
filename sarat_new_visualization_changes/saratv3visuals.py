#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 11:37:04 2026

@author: arkaprava
"""

id_number=6687

# %%####this will be required as input in the form of string [comment to run the code as function]
import sys
import os
path='/home/arkaprava/INCOIS_ARO/SARAT_V3_Visualization/'

inputpath= os.path.join(path, f"case{id_number}/")

# inputpath=f'/home/arkaprava/INCOIS_ARO/may2025/combination3186/case7070_31_24_26_c7052/case{id_number}/'
sys.path.append(inputpath)

functionpath='/home/arkaprava/INCOIS_ARO/SARAT_V3_Visualization/pyfunc/'


outputpath=os.path.join(path, f"case{id_number}/figure/")

# outputpath=f'/home/arkaprava/INCOIS_ARO/may2025/combination3186/case7070_31_24_26_c7052/case{id_number}/figure/'


sys.path.append(functionpath)
import sarat_visuals
import allin1sarat

# %%


# put all the names of files required to run the code
# currentfile= os.path.join(inputpath,"current9620.nc")
# drifterfile=os.path.join(inputpath,"drifter9428.txt")
# completetraj=os.path.join(inputpath,"complete_traj_9428.dat")



# %%
results=allin1sarat.run_sarat_analysis(id_number, input_path=inputpath,num_trajectories=500, interval_size=24, plot_sighted_positions=False,beacontrack=False)

for key, value in results.items():
    globals()[key] = value
    
for key, value in grid_meta.items():
    globals()[key] = value


plot_beacon_track = beacon_lon is not None and beacon_lat is not None


with open(os.path.join(outputpath,"bounding_rect_and_centroid.txt"), "w") as coord_file:
    coord_file.write("Interval,Rect_BottomLeft_Lon,Rect_BottomLeft_Lat,Rect_TopRight_Lon,Rect_TopRight_Lat,Latest_Centroid_Lon,Latest_Centroid_Lat\n")


# %%
xlow=80
xhigh=84
ylow=4
yhigh=6
# %%
##the variable name in the current file is differnet than usual, which are changed in the main function code.

sarat_visuals.plot_individual(outputpath,intervals, trajectories, centroids, ds_hourly, 
                             lon_bins, lat_bins, max_prob_global, 
                             sighted_positions=sighted_positions,
                             plot_beacon_track=False,plot_individual=True,xylimit=False,
                             plot_sighted_positions=True,reference_vector_length = 0.5, 
                             output_prefix="seeding")


# sarat_visuals.plot_individual(outputpath,intervals, trajectories, centroids, ds_hourly, 
#                              lon_bins, lat_bins,max_prob_global,beacon_time,beacon_lon,beacon_lat,
#                              xlow=xlow,xhigh=xhigh,ylow=ylow,yhigh=yhigh,
#                              plot_beacon_track=True,plot_individual=True,xylimit=True,
#                              plot_sighted_positions=False,reference_vector_length = 0.5, 
#                              output_prefix="seeding")

###if there is drifter plot_beacon_track=False--make this True and add beacon_time,beacon_lon,beacon_lat (in this seq) after max_prob_global
### check the actual function and change accordingly in different cases. 


sarat_visuals.plot_combined(outputpath,id_number,intervals, trajectories, centroids, ds_hourly, 
                             lon_bins, lat_bins,max_prob_global,
                             sighted_positions=sighted_positions,
                             plot_beacon_track=False,plot_combined=True,xylimit=False,plot_sighted_positions=True,reference_vector_length = 0.5, 
                             output_prefix="seeding")

# sarat_visuals.plot_combined(outputpath,id_number,intervals, trajectories, centroids, ds_hourly, 
#                              lon_bins, lat_bins,max_prob_global,beacon_time,beacon_lon,beacon_lat, 
#                              xlow=xlow,xhigh=xhigh,ylow=ylow,yhigh=yhigh, 
#                              plot_beacon_track=True,plot_combined=True,xylimit=True,
#                              plot_sighted_positions=False,reference_vector_length = 0.5, 
#                              output_prefix="seeding")


