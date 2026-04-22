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

# ---------------------------------------------------------------------------
# Helper: Dynamically truncate a coordinate to max 6 decimal places cleanly
# operating purely on strings to avoid IEEE float auto-rounding artifacts
# like "69.832999999..." involuntarily rounding up to 69.833 natively.
# ---------------------------------------------------------------------------
def round_coord(value):
    """Truncate to up to 6 decimal places dynamically."""
    s = str(value)
    idx = s.find('.')
    if idx != -1 and len(s) > idx + 7:
        s = s[:idx+7]
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
    
    min_lon, max_lon = float('inf'), float('-inf')
    min_lat, max_lat = float('inf'), float('-inf')
    points_included = 0
    max_prob = 0
    
    for i in range(prob_grid.shape[0]):  # lat dimension
        for j in range(prob_grid.shape[1]):  # lon dimension
            prob_value = prob_grid[i][j]
            
            if prob_value > threshold:
                # Use the cell's physical bin edges
                min_lon = min(min_lon, lon_bins[j])
                max_lon = max(max_lon, lon_bins[j+1])
                min_lat = min(min_lat, lat_bins[i])
                max_lat = max(max_lat, lat_bins[i+1])
                
                points_included += 1
                coords.append([truncate(lon), truncate(lat)])
                max_prob = max(max_prob, prob_value)
    
    # Need at least 1 point for bounding rectangle
    if points_included == 0:
        print(f"  ⚠️  Interval {interval_label}: 0 points above threshold - skipping rectangle")
        return None
    
    # Compute bounding rectangle
    try:
        polygon_coords = [
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]
        
        # Round every vertex coordinate to 6 decimal places before writing
        # GeoJSON to avoid unnecessary floating-point noise in the output.
        polygon_coords = [[round_coord(v[0]), round_coord(v[1])] for v in polygon_coords]
        
        # Approximate area of the bounding box
        box_area = (max_lon - min_lon) * (max_lat - min_lat)
        
        # Create GeoJSON Feature
        geojson = {
            "type": "Feature",
            "properties": {
                "interval": interval_label,
                "points_included": points_included,
                "max_probability": round(float(max_prob), 4),
                "hull_area": round(float(box_area), 4)  # 2D box area
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            }
        }
        
        return geojson
    
    except Exception as e:
        print(f"  ✗ Error computing rectangle for {interval_label}: {e}")
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
                        # Round coordinates to 6 decimal places
                        "coordinates": [round_coord(lon), round_coord(lat)]
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
