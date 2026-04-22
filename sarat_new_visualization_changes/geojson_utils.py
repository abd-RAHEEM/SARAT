#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoJSON Utilities for SARAT v3
Handles convex hull computation and GeoJSON polygon generation
"""

import json
import numpy as np
from scipy.spatial import ConvexHull


def truncate(val):
    """Truncate float to 6 decimal places"""
    s = str(val)
    if '.' in s:
        i = s.find('.')
        return float(s[:i+7])
    return float(s)


def create_hull_geojson(prob_grid, lon_bins, lat_bins, interval_label, threshold=0.05):
    """
    Convert probability grid → convex hull polygon GeoJSON
    
    Creates a search region boundary that encloses all high-probability areas.
    
    Parameters
    ----------
    prob_grid : np.ndarray
        2D array of probabilities (rows=lat, cols=lon)
    lon_bins : np.ndarray
        Longitude bin edges
    lat_bins : np.ndarray
        Latitude bin edges
    interval_label : str
        Human-readable interval label (e.g., "0-24h")
    threshold : float
        Only include cells with probability > threshold (default: 0.05%)
    
    Returns
    -------
    dict or None
        GeoJSON Feature with Polygon geometry, or None if insufficient points
    """
    
    # Extract coordinates of cells above threshold
    coords = []
    max_prob = 0
    
    for i in range(prob_grid.shape[0]):  # lat dimension
        for j in range(prob_grid.shape[1]):  # lon dimension
            prob_value = prob_grid[i][j]
            
            if prob_value > threshold:
                # Calculate cell center
                lon = (lon_bins[j] + lon_bins[j+1]) / 2.0
                lat = (lat_bins[i] + lat_bins[i+1]) / 2.0
                
                coords.append([truncate(lon), truncate(lat)])
                max_prob = max(max_prob, prob_value)
    
    # Need at least 3 points for convex hull
    if len(coords) < 3:
        print(f"  ⚠️  Interval {interval_label}: Only {len(coords)} points above threshold - skipping hull")
        return None
    
    # Compute convex hull
    try:
        points = np.array(coords)
        hull = ConvexHull(points)
        
        # Extract hull vertices (ordered)
        polygon_coords = points[hull.vertices].tolist()
        
        # Close the polygon
        polygon_coords.append(polygon_coords[0])
        
        # Create GeoJSON Feature
        geojson = {
            "type": "Feature",
            "properties": {
                "interval": interval_label,
                "points_included": len(coords),
                "max_probability": round(float(max_prob), 4),
                "hull_area": round(float(hull.volume), 4)  # 2D "volume" is area
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            }
        }
        
        return geojson
    
    except Exception as e:
        print(f"  ✗ Error computing hull for {interval_label}: {e}")
        return None


def create_points_geojson(prob_grid, lon_bins, lat_bins, interval_label, threshold=0.05):
    """
    Convert probability grid → points FeatureCollection GeoJSON
    
    This is the fallback/alternative to hull - returns scattered points instead.
    Useful for comparison or when hull fails.
    
    Parameters
    ----------
    prob_grid : np.ndarray
        2D probability array
    lon_bins : np.ndarray
        Longitude bins
    lat_bins : np.ndarray
        Latitude bins
    interval_label : str
        Interval label
    threshold : float
        Probability threshold
    
    Returns
    -------
    dict
        FeatureCollection with Point features
    """
    
    features = []
    
    for i in range(prob_grid.shape[0]):
        for j in range(prob_grid.shape[1]):
            prob_value = prob_grid[i][j]
            
            if prob_value >= threshold:
                lon = (lon_bins[j] + lon_bins[j+1]) / 2.0
                lat = (lat_bins[i] + lat_bins[i+1]) / 2.0
                
                feature = {
                    "type": "Feature",
                    "properties": {
                        "interval": interval_label,
                        "probability": round(float(prob_value), 4),
                        "probability_percent": round(float(prob_value), 2)
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    }
                }
                features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "properties": {
            "interval": interval_label,
            "feature_count": len(features)
        },
        "features": features
    }
    
    return geojson


def save_geojson(geojson_data, filepath):
    """
    Save GeoJSON to file
    
    Parameters
    ----------
    geojson_data : dict
        GeoJSON object
    filepath : str
        Output file path
    """
    
    with open(filepath, "w") as f:
        json.dump(geojson_data, f, indent=2)


def create_geojson_index(geojson_files, intervals, case_id):
    """
    Create an index file for GeoJSON discovery
    
    Parameters
    ----------
    geojson_files : list
        List of GeoJSON filenames
    intervals : list
        List of [start, end] hour tuples
    case_id : str or int
        Case identifier
    
    Returns
    -------
    dict
        Index data structure
    """
    
    import datetime
    
    index = {
        "version": "1.0",
        "case_id": str(case_id),
        "generated": datetime.datetime.now().isoformat(),
        "total_intervals": len(geojson_files),
        "files": geojson_files,
        "intervals": intervals,
        "geometry_type": "polygon"  # Indicate hulls, not points
    }
    
    return index


if __name__ == "__main__":
    """
    Quick test of convex hull generation
    """
    print("GeoJSON Utilities - SARAT v3")
    print("=" * 50)
    
    # Create dummy data
    prob_grid = np.random.rand(10, 10) * 5  # 0-5% probability
    lon_bins = np.linspace(80, 85, 11)
    lat_bins = np.linspace(10, 15, 11)
    
    # Test hull generation
    hull_geojson = create_hull_geojson(prob_grid, lon_bins, lat_bins, "0-24h")
    
    if hull_geojson:
        print("✓ Convex hull generated successfully")
        print(f"  Polygon has {len(hull_geojson['geometry']['coordinates'][0])} vertices")
    else:
        print("✗ Hull generation failed")
