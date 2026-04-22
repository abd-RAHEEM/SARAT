import json
import sys
import os

def is_float(value):
   try:
       float(value)
       return True
   except ValueError:
       return False

# ---------------------------------------------------------------------------
# Helper: Dynamically truncate a coordinate to max 6 decimal places cleanly
# operating purely on strings to avoid IEEE float auto-rounding artifacts
# like "69.832999999..." involuntarily rounding up to 69.833 natively.
# ---------------------------------------------------------------------------
def round_coord(value):
    """Truncate a latitude or longitude dynamically up to 6 decimal places."""
    s = str(value)
    # Check if decimal exists and slice exactly to retain truncation organically
    idx = s.find('.')
    if idx != -1 and len(s) > idx + 7:
        s = s[:idx+7]
    return float(s)

def createLKPGeoJson(uniqId, searchAndRescueRootDir):
    # finalConvexHullDatFile = os.path.join(searchAndRescueRootDir, f"finalconvexhull_{uniqId}.dat")
    hullDatFile = os.path.join(searchAndRescueRootDir, f"hull_{uniqId}.dat")
   
    lkpCoordinates = []

    # if os.path.getsize(finalConvexHullDatFile) > 0:
    if os.path.exists(hullDatFile) and os.path.getsize(hullDatFile) > 0:
        # Only if the hull file is not empty
        # with open(finalConvexHullDatFile, "r") as f:
        try:
            with open(hullDatFile, "r") as f:
                firstLine = f.readline().strip()
                lon, lat = firstLine.split()
                if not is_float(lon):
                    print(f"Longitude {lon} is expected to be a float. {type(lon)}")
                elif not is_float(lat):
                    print(f"Latitude {lat} is expected to be a float.")
                else:
                    # Round coordinates to 6 decimal places before storing
                    lkpCoordinates = [round_coord(lon), round_coord(lat)]
        except Exception as ex:
            print(f"Error while generating LKP geojson file from {hullDatFile}: {str(ex)}")

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": lkpCoordinates
        },
        "properties": {
            "name": "Last Known Position"
        }
    }

    featureCollection = {
        "type": "FeatureCollection",
        "features": [feature]
    }

    lkpGeoJson = os.path.join(searchAndRescueRootDir, f"lkp_{uniqId}.geojson")
    with open(lkpGeoJson, "wt") as f:
        json.dump(featureCollection, f, indent=4)

def createTrajectoriesGeoJson(uniqId, searchAndRescueRootDir):
    trajectoriesDatFile = os.path.join(searchAndRescueRootDir, f"complete_traj_{uniqId}.dat")

    features = []
    try:
        with open(trajectoriesDatFile, 'r') as f:
            # coordinates = []
            index = 1
            trajectoryCoordinates = []
            for line in f:            
                if len(line.strip()) > 0:
                    lon, lat = line.split()
                    # Round each coordinate to 6 decimal places to keep
                    # GeoJSON file size reasonable without losing precision
                    trajectoryCoordinates.append([round_coord(lon), round_coord(lat)])
                else:
                    # Empty line; end of the line string
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": trajectoryCoordinates
                        },
                        "properties":{
                            "name": f"Trajectory_{index}"
                        }
                    }                
                    index = index + 1
                    features.append(feature)
                    trajectoryCoordinates = []

            # Last trajectory
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": trajectoryCoordinates
                },
                "properties":{
                    "name": f"Trajectory_{index}"
                }
            }
            features.append(feature)
            trajectoryCoordinates = []
    except Exception as ex:
        print(f"Error while generating trajectories geojson from {trajectoriesDatFile}: {str(ex)}")

    # Create a GeoJSON FeatureCollection
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    # Write the GeoJSON to a file
    trajectoriesGeoJsonFile = os.path.join(searchAndRescueRootDir, f"trajectories_{uniqId}.geojson")
    with open(trajectoriesGeoJsonFile, 'w') as f:
        json.dump(feature_collection, f, indent=4)

def createMeanTrajectoryGeoJson(uniqId, searchAndRescueRootDir):
    meanTrajectoryFile = os.path.join(searchAndRescueRootDir, f"meantrajectory_{uniqId}.dat")
    features = []

    try:
        with open(meanTrajectoryFile, 'r') as f:
            meanTrajectoryCoordinates = []
            for line in f:            
                if len(line.strip()) > 0:
                    lon, lat = line.split()
                    # Round to 6 decimal places (raw strings from .dat file
                    # may have excess precision; convert to float first)
                    meanTrajectoryCoordinates.append([round_coord(lon), round_coord(lat)])

            # Empty line; end of the line string
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": meanTrajectoryCoordinates
                },
                "properties":{
                    "name": f"MeanTrajectory"
                }
            }       
            features.append(feature)
    except Exception as ex:
        print(f"Error while generating mean trajectory geojson from {meanTrajectoryFile}: {str(ex)}")
    

    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    # Write the GeoJSON to a file
    meanTrajectoryJson = os.path.join(searchAndRescueRootDir, f"meantrajectory_{uniqId}.geojson")
    with open(meanTrajectoryJson, 'w') as f:
        json.dump(feature_collection, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Atleast two arguments expected. Got {len(sys.argv)} arguments.")
        print(f"Usage: {sys.argv[0]} <Uniq_Id> <Search_And_Rescue_Root_Dir>")
        print(f"Uniq_Id argument specifies the unique-id that was assigned by the SARAT application system.")
        print(f"Search_And_Rescue_Root_Dir argument specifies the directory in which Leeway model outputs can be found and where the output geojsons are written.")
        sys.exit(2)

    uniqId = sys.argv[1]
    searchAndRescueRootDir = sys.argv[2]

    createMeanTrajectoryGeoJson(uniqId, searchAndRescueRootDir)
    createTrajectoriesGeoJson(uniqId, searchAndRescueRootDir)
    createLKPGeoJson(uniqId, searchAndRescueRootDir)

    # trajectories_file = f"complete_traj_{uniqId}.dat"
    # trajectories_output_geojson = f"trajectories_{uniqId}.geojson"
    # create_trajectories_geojson(trajectories_file, trajectories_output_geojson)