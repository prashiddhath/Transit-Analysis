"""
Singapore MRT/LRT Network Analysis
Computes FRI (Functional Resilience Index) and SME (System Level Mobility Efficiency)
Based on Derrible & Kennedy (2009) methodology
"""

import pandas as pd
import networkx as nx
import numpy as np
import os
from datetime import datetime
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Try to import visualization libraries
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available, visualizations will be skipped")

# ==================================================================================
# CONFIGURATION
# ==================================================================================

DATA_DIR = "input/singapore_2009"
OUTPUT_DIR = "outputs/singapore_2009"

# Singapore parameters
SINGAPORE_POPULATION = 5_453_600  # 2024 estimate
SINGAPORE_AREA = 734.3  # km²

# Travel parameters
WALKING_SPEED = 5.0  # km/h
TRANSFER_TIME = 2.0  # minutes
AVG_STATION_SPACING = 1.2  # km (estimate)

# SME time thresholds
SME_TIME_THRESHOLDS = [20, 30, 45, 60]  # minutes

# FRI disruption scenarios
RANDOM_FAILURE_PROBS = [0.05, 0.10, 0.15, 0.20]  # Probabilities for random failures
RANDOM_SCENARIOS_PER_PROB = 10  # Number of random scenarios per probability
TARGETED_FAILURE_COUNTS = [1, 2, 3, 4, 5, 6, 7, 8]  # Number of stations to remove in targeted failures

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================================================================================
# DATA LOADING
# ==================================================================================

def load_singapore_data():
    """Load Singapore MRT/LRT GTFS data"""
    print("=" * 80)
    print("LOADING SINGAPORE MRT/LRT DATA")
    print("=" * 80)
    
    # Standard GTFS filenames
    routes = pd.read_csv(os.path.join(DATA_DIR, "routes.txt"))
    trips = pd.read_csv(os.path.join(DATA_DIR, "trips.txt"))
    stop_times = pd.read_csv(os.path.join(DATA_DIR, "stop_times.txt"))
    stops = pd.read_csv(os.path.join(DATA_DIR, "stops.txt"))
    
    # Filter for MRT/LRT only (route_type == 1)
    mrt_routes = routes[routes['route_type'] == 1].copy()
    mrt_trip_ids = trips[trips['route_id'].isin(mrt_routes['route_id'])]['trip_id']
    mrt_trips = trips[trips['trip_id'].isin(mrt_trip_ids)].copy()
    mrt_stop_times = stop_times[stop_times['trip_id'].isin(mrt_trip_ids)].copy()
    
    # Get unique stops used by MRT
    mrt_stop_ids = mrt_stop_times['stop_id'].unique()
    mrt_stops = stops[stops['stop_id'].isin(mrt_stop_ids)].copy()
    
    print(f"\nTotal routes: {len(routes)} (filtered to {len(mrt_routes)} MRT/LRT lines)")
    print(f"MRT/LRT trips: {len(mrt_trips)}")
    print(f"MRT/LRT stop times: {len(mrt_stop_times)}")
    print(f"MRT/LRT stops: {len(mrt_stops)}")
    
    return mrt_routes, mrt_trips, mrt_stop_times, mrt_stops


def parse_time(time_str):
    """Parse GTFS time string (HH:MM:SS) to minutes since midnight"""
    parts = time_str.split(':')
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    return hours * 60 + minutes + seconds / 60


def identify_unique_stations(stops):
    """
    Identify unique stations by grouping stops with the same name or parent_station
    Returns a mapping from stop_id to station_id
    """
    print("\n" + "-" * 80)
    print("IDENTIFYING UNIQUE STATIONS")
    print("-" * 80)
    
    # Group by parent_station if available, otherwise by stop_name
    station_groups = defaultdict(list)
    
    for idx, row in stops.iterrows():
        # Use parent_station if available, otherwise use the stop name
        if 'parent_station' in stops.columns and pd.notna(row.get('parent_station')) and row.get('parent_station') != '':
            station_key = str(row['parent_station'])
        else:
            # Clean station name (remove platform info in parentheses)
            name = row['stop_name']
            if '(' in name:
                name = name[:name.index('(')].strip()
            station_key = name
        
        station_groups[station_key].append({
            'stop_id': row['stop_id'],
            'stop_name': row['stop_name'],
            'lat': row['stop_lat'],
            'lon': row['stop_lon']
        })
    
    # Create mapping from stop_id to station_id
    stop_to_station = {}
    stations = []
    
    for station_id, (station_key, stop_list) in enumerate(station_groups.items()):
        # Use average coordinates for the station
        avg_lat = np.mean([s['lat'] for s in stop_list])
        avg_lon = np.mean([s['lon'] for s in stop_list])
        
        # Use the shortest name as the station name
        names = [s['stop_name'] for s in stop_list]
        station_name = min(names, key=len)
        if '(' in station_name:
            station_name = station_name[:station_name.index('(')].strip()
        
        stations.append({
            'station_id': station_id,
            'station_name': station_name,
            'lat': avg_lat,
            'lon': avg_lon,
            'stop_ids': [s['stop_id'] for s in stop_list]
        })
        
        for stop in stop_list:
            stop_to_station[stop['stop_id']] = station_id
    
    stations_df = pd.DataFrame(stations)
    print(f"Total unique stations: {len(stations_df)}")
    
    return stations_df, stop_to_station


def calculate_travel_times(stop_times, trips):
    """
    Calculate average travel times between consecutive stops on each trip
    Returns a dictionary of (stop1, stop2) -> average_time_minutes
    """
    print("\n" + "-" * 80)
    print("CALCULATING TRAVEL TIMES")
    print("-" * 80)
    
    # Merge with trips to get route information
    stop_times_with_route = stop_times.merge(trips[['trip_id', 'route_id']], on='trip_id')
    
    travel_times = defaultdict(list)
    
    # Sort by trip and sequence
    stop_times_with_route = stop_times_with_route.sort_values(['trip_id', 'stop_sequence'])
    
    # Calculate travel times between consecutive stops
    for trip_id, trip_data in stop_times_with_route.groupby('trip_id'):
        trip_data = trip_data.sort_values('stop_sequence')
        
        for i in range(len(trip_data) - 1):
            current = trip_data.iloc[i]
            next_stop = trip_data.iloc[i + 1]
            
            # Parse times
            try:
                dep_time = parse_time(current['departure_time'])
                arr_time = parse_time(next_stop['arrival_time'])
                
                # Handle times that cross midnight
                if arr_time < dep_time:
                    arr_time += 24 * 60
                
                travel_time = arr_time - dep_time
                
                if travel_time > 0 and travel_time < 30:  # Sanity check: between 0 and 30 minutes
                    stop1 = current['stop_id']
                    stop2 = next_stop['stop_id']
                    travel_times[(stop1, stop2)].append(travel_time)
                    travel_times[(stop2, stop1)].append(travel_time)  # Bidirectional
            except:
                continue
    
    # Average the travel times
    avg_travel_times = {}
    for edge, times in travel_times.items():
        avg_travel_times[edge] = np.mean(times)
    
    print(f"Calculated travel times for {len(avg_travel_times)} stop pairs")
    
    return avg_travel_times


# ==================================================================================
# NETWORK CONSTRUCTION
# ==================================================================================

def build_network_topology(routes, trips, stop_times, stations_df, stop_to_station, avg_travel_times):
    """
    Build network topology: identify which lines serve which stations,
    and which stations are connected
    """
    print("\n" + "-" * 80)
    print("BUILDING NETWORK TOPOLOGY")
    print("-" * 80)
    
    # Get unique route names (some routes have multiple route_ids)
    # Singapore uses route_short_name (BP, CC, DT, etc.)
    routes['route_name'] = routes['route_short_name']
    unique_routes = routes.groupby('route_name')['route_id'].apply(list).reset_index()
    
    print(f"Unique lines: {list(unique_routes['route_name'])}")
    
    # Determine which stations each line serves
    line_stations = defaultdict(set)
    station_lines = defaultdict(set)
    
    # Build edges with line information
    edges = defaultdict(lambda: {'lines': set(), 'travel_time': None})
    
    for route_name, route_ids in zip(unique_routes['route_name'], unique_routes['route_id']):
        # Get all trips for this line
        line_trips = trips[trips['route_id'].isin(route_ids)]['trip_id']
        line_stop_times = stop_times[stop_times['trip_id'].isin(line_trips)]
        
        # Use ALL trips to get complete line topology (not just first trip)
        # Group by stop sequence to get all stations served
        for trip_id in line_trips.unique():  # Process all trips
            trip_stops = line_stop_times[line_stop_times['trip_id'] == trip_id].sort_values('stop_sequence')
            
            prev_station = None
            prev_stop_id = None
            for _, stop in trip_stops.iterrows():
                station_id = stop_to_station.get(stop['stop_id'])
                if station_id is not None:
                    line_stations[route_name].add(station_id)
                    station_lines[station_id].add(route_name)
                    
                    # Add edge to previous station
                    if prev_station is not None and prev_station != station_id:
                        edge = tuple(sorted([prev_station, station_id]))
                        edges[edge]['lines'].add(route_name)
                        
                        # Get travel time if available (only set once per edge)
                        if edges[edge]['travel_time'] is None and prev_stop_id is not None:
                            stop1 = stop['stop_id']
                            stop2 = prev_stop_id
                            if (stop2, stop1) in avg_travel_times:
                                edges[edge]['travel_time'] = avg_travel_times[(stop2, stop1)]
                            elif (stop1, stop2) in avg_travel_times:
                                edges[edge]['travel_time'] = avg_travel_times[(stop1, stop2)]
                    
                    prev_station = station_id
                    prev_stop_id = stop['stop_id']
    
    # FIRST PASS: Identify transfer and terminal stations
    # Transfer = served by multiple lines
    transfer_stations = {sid for sid, lines in station_lines.items() if len(lines) >= 2}
    
    # Terminal = endpoints of each line (degree = 1 on that line's segment graph)
    terminal_stations = set()
    for route_name, station_set in line_stations.items():
        # For each line, find stations that only have one edge on that line
        line_edges = {edge for edge, data in edges.items() if route_name in data['lines']}
        station_degree_on_line = defaultdict(int)
        for edge in line_edges:
            station_degree_on_line[edge[0]] += 1
            station_degree_on_line[edge[1]] += 1
        
        # Terminals have degree 1 on a line
        for station, degree in station_degree_on_line.items():
            if degree == 1:
                terminal_stations.add(station)
    
    # Special vertices for D&K model
    special_vertices = transfer_stations | terminal_stations
    
    print(f"\nIdentified {len(transfer_stations)} transfer and {len(terminal_stations)} terminal stations")
    print(f"Total special vertices for D&K model: {len(special_vertices)}")
    
    # SECOND PASS: Build edges ONLY between special vertices (D&K simplified model)
    # For each line, connect consecutive transfer/terminal vertices, skipping intermediates
    dk_edges = defaultdict(lambda: {'lines': set(), 'travel_time': None})
    
    for route_name, route_ids in zip(unique_routes['route_name'], unique_routes['route_id']):
        line_trips = trips[trips['route_id'].isin(route_ids)]['trip_id']
        line_stop_times = stop_times[stop_times['trip_id'].isin(line_trips)]
        
        # Process ALL trips to capture all line variants and shared segments
        for trip_id in line_trips.unique():
            trip_stops = line_stop_times[line_stop_times['trip_id'] == trip_id].sort_values('stop_sequence')
            
            # Filter to only special vertices, maintaining order
            special_stops_in_order = []
            
            for _, stop in trip_stops.iterrows():
                station_id = stop_to_station.get(stop['stop_id'])
                if station_id is not None and station_id in special_vertices:
                    # Avoid consecutive duplicates
                    if not special_stops_in_order or special_stops_in_order[-1][0] != station_id:
                        special_stops_in_order.append((station_id, stop['stop_id']))
            
            # Create edges between consecutive special vertices
            for i in range(len(special_stops_in_order) - 1):
                current_station_id, current_stop_id = special_stops_in_order[i]
                next_station_id, next_stop_id = special_stops_in_order[i + 1]
                
                edge = tuple(sorted([current_station_id, next_station_id]))
                dk_edges[edge]['lines'].add(route_name)
                
                # Get travel time if available
                if dk_edges[edge]['travel_time'] is None:
                    if (current_stop_id, next_stop_id) in avg_travel_times:
                        dk_edges[edge]['travel_time'] = avg_travel_times[(current_stop_id, next_stop_id)]
                    elif (next_stop_id, current_stop_id) in avg_travel_times:
                        dk_edges[edge]['travel_time'] = avg_travel_times[(next_stop_id, current_stop_id)]
    
    # CRITICAL FIX: Ensure all special vertices have at least one edge
    # Some terminals may be isolated if they're the last stop in all trips and missing reverse trips
    print(f"\n  Post-processing: Checking for isolated terminals...")
    
    # Build adjacency list from edges
    vertex_edges = defaultdict(set)
    for edge in dk_edges.keys():
        s1, s2 = edge
        vertex_edges[s1].add(edge)
        vertex_edges[s2].add(edge)
    
    # Find isolated vertices
    isolated_vertices = [v for v in special_vertices if v not in vertex_edges or len(vertex_edges[v]) == 0]
    
    if isolated_vertices:
        print(f"  Found {len(isolated_vertices)} isolated terminals - connecting them...")
        
        for isolated_vertex in isolated_vertices:
            # Find which lines this vertex is on
            vertex_lines = station_lines.get(isolated_vertex, set())
            
            # For each line, find the nearest special vertex on that line
            for line_name in vertex_lines:
                # Get all special vertices on this line
                line_special_vertices = [v for v in special_vertices 
                                        if line_name in station_lines.get(v, set())]
                
                # Find one that already has edges (part of the network)
                connected_vertices = [v for v in line_special_vertices 
                                     if v in vertex_edges and len(vertex_edges[v]) > 0]
                
                if connected_vertices:
                    # Connect to the first connected vertex on this line
                    # (In reality, should be "nearest" but for terminal fix, any connection works)
                    nearest_vertex = connected_vertices[0]
                    
                    edge = tuple(sorted([isolated_vertex, nearest_vertex]))
                    if edge not in dk_edges:
                        dk_edges[edge]['lines'].add(line_name)
                        dk_edges[edge]['travel_time'] = None  # Will estimate later
                        print(f"    Connected {isolated_vertex} to {nearest_vertex} via {line_name}")
                        break
    else:
        print(f"  All {len(special_vertices)} special vertices are connected ✓")
    
    # Count edges according to D&K: parallel edges count separately
    # If an edge has multiple lines, it contributes 1 single + 1 multiple
    single_use_count = 0
    multiple_use_count = 0
    
    for edge, data in dk_edges.items():
        num_lines_on_edge = len(data['lines'])
        if num_lines_on_edge > 1:
            # Parallel edge - counts as 1 single + 1 multiple
            single_use_count += 1
            multiple_use_count += 1
        else:
            # Single line - counts as 1 single
            single_use_count += 1
    
    # Calculate route lengths (still use full network for this)
    route_lengths = {}
    total_length = 0
    
    for route_name, route_stations in line_stations.items():
        # Calculate length by summing distances of edges on this route
        route_edges = {edge for edge, data in edges.items() if route_name in data['lines']}
        route_length = 0
        for edge in route_edges:
            s1, s2 = edge
            lat1 = stations_df[stations_df['station_id'] == s1]['lat'].values[0]
            lon1 = stations_df[stations_df['station_id'] == s1]['lon'].values[0]
            lat2 = stations_df[stations_df['station_id'] == s2]['lat'].values[0]
            lon2 = stations_df[stations_df['station_id'] == s2]['lon'].values[0]
            
            # Haversine distance
            dist_km = haversine_distance(lat1, lon1, lat2, lon2)
            route_length += dist_km
        
        route_lengths[route_name] = route_length
        total_length += route_length
    
    total_dk_edges = single_use_count + multiple_use_count
    
    print(f"\nD&K Simplified Topology:")
    print(f"  Total stations (all): {len(stations_df)}")
    print(f"  Transfer vertices (v^t): {len(transfer_stations)}")
    print(f"  Terminal vertices (v^e): {len(terminal_stations)}")
    print(f"  Special vertices in graph: {len(special_vertices)}")
    print(f"  Total edges (e): {total_dk_edges}")
    print(f"  Single-use edges (e^s): {single_use_count}")
    print(f"  Multiple-use edges (e^m): {multiple_use_count}")
    print(f"  Total route length: {total_length:.2f} km")
    
    return {
        'line_stations': dict(line_stations),
        'station_lines': dict(station_lines),
        'edges': dict(dk_edges),  # Use D&K simplified edges
        'all_edges': dict(edges),  # Keep full edges for SME/travel time
        'transfer_stations': transfer_stations,
        'terminal_stations': terminal_stations,
        'special_vertices': special_vertices,
        'single_use_count': single_use_count,
        'multiple_use_count': multiple_use_count,
        'route_lengths': route_lengths,
        'total_length': total_length,
        'num_lines': len(unique_routes)
    }


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c


def create_networkx_graph(stations_df, topology, stop_to_station, avg_travel_times, for_fri=False):
    """
    Create NetworkX graph
    If for_fri=True, include all stations but mark transfer and terminals for metric calculation
    Otherwise, include all stations with travel times for SME
    """
    G = nx.Graph()
    
    if for_fri:
        # FRI graph: D&K simplified model - ONLY transfer and terminal vertices
        special_vertices = topology.get('special_vertices', set())
        
        for _, station in stations_df.iterrows():
            station_id = station['station_id']
            # Only add special vertices to FRI graph
            if station_id in special_vertices:
                G.add_node(station_id, 
                          name=station['station_name'],
                          is_transfer=station_id in topology['transfer_stations'],
                          is_terminal=station_id in topology['terminal_stations'],
                          lines=topology['station_lines'].get(station_id, set()))
        
        # Add D&K simplified edges (only between special vertices)
        for edge, edge_data in topology['edges'].items():
            s1, s2 = edge
            # Distance for FRI
            lat1 = stations_df[stations_df['station_id'] == s1]['lat'].values[0]
            lon1 = stations_df[stations_df['station_id'] == s1]['lon'].values[0]
            lat2 = stations_df[stations_df['station_id'] == s2]['lat'].values[0]
            lon2 = stations_df[stations_df['station_id'] == s2]['lon'].values[0]
            dist = haversine_distance(lat1, lon1, lat2, lon2)
            
            G.add_edge(s1, s2,
                      lines=edge_data['lines'],
                      distance=dist,
                      is_multiple_use=len(edge_data['lines']) > 1)
    else:
        # Full graph: all stations with travel times (for SME)
        for _, station in stations_df.iterrows():
            station_id = station['station_id']
            G.add_node(station_id,
                      name=station['station_name'],
                      lat=station['lat'],
                      lon=station['lon'],
                      lines=topology['station_lines'].get(station_id, set()))
        
        # Add edges with travel times - use ALL edges, not D&K simplified
        all_edges = topology.get('all_edges', topology['edges'])
        for edge, edge_data in all_edges.items():
            s1, s2 = edge
            
            # Get travel time
            travel_time = edge_data['travel_time']
            if travel_time is None:
                # Estimate from distance
                lat1 = stations_df[stations_df['station_id'] == s1]['lat'].values[0]
                lon1 = stations_df[stations_df['station_id'] == s1]['lon'].values[0]
                lat2 = stations_df[stations_df['station_id'] == s2]['lat'].values[0]
                lon2 = stations_df[stations_df['station_id'] == s2]['lon'].values[0]
                dist = haversine_distance(lat1, lon1, lat2, lon2)
                travel_time = (dist / AVERAGE_SUBWAY_SPEED_KMH) * 60  # Convert to minutes
            
            G.add_edge(s1, s2,
                      travel_time=travel_time,
                      lines=edge_data['lines'],
                      is_multiple_use=len(edge_data['lines']) > 1)
    
    return G


# ==================================================================================
# FRI (FUNCTIONAL RESILIENCE INDEX) CALCULATIONS
# ==================================================================================

def compute_derrible_kennedy_indicators(G, topology, total_length, num_lines):
    """
    Compute Derrible & Kennedy indicators:
    - Coverage (σ)
    - Directness (τ)
    - Connectivity (ρ)
    
    Uses D&K simplified topology with edges only between transfer/terminal vertices
    
    Per D&K: "one end vertex that is also a transfer vertex is considered to be only a transfer vertex"
    """
    
    # Number of vertices - use from topology
    # CRITICAL: If a station is both transfer AND terminal, count it ONLY as transfer!
    all_transfer_stations = topology['transfer_stations']
    all_terminal_stations = topology['terminal_stations']
    
    # Terminals that are NOT also transfers
    terminal_only = all_terminal_stations - all_transfer_stations
    
    v_t = len(all_transfer_stations)  # Transfer vertices
    v_e = len(terminal_only)  # End vertices (terminals that are NOT transfers)
    v = v_t + v_e  # Total vertices per Derrible & Kennedy
    
    # Number of edges - use counts from topology (D&K simplified model)
    e = topology['single_use_count'] + topology['multiple_use_count']
    e_s = topology['single_use_count']
    e_m = topology['multiple_use_count']
    
    # 1. Coverage (σ)
    # σ = (n_s × π × 0.5²) / A
    # where n_s is number of ALL stations (not just special vertices)
    A = SINGAPORE_AREA
    n_s_total = len(topology['station_lines'])  # Total number of all stations
    coverage_radius_km = 0.5  # 500m radius
    sigma = (n_s_total * np.pi * coverage_radius_km**2) / A
    
    # 2. Directness (τ)
    # τ = n_L / δ
    # δ = maximum number of line TRANSFERS needed
    # We use BFS to find minimum transfers between all pairs of transfer/terminal stations
    
    def count_min_transfers_bfs(G, source, target):
        """Count minimum number of line transfers from source to target using BFS"""
        from collections import deque
        
        # BFS with state = (current_station, current_line, num_transfers)
        queue = deque()
        visited = {}  # (station, line) -> min_transfers
        
        # Start from source - can board any line available there
        source_lines = G.nodes[source].get('lines', set())
        for line in source_lines:
            queue.append((source, line, 0))
            visited[(source, line)] = 0
        
        min_transfers_to_target = float('inf')
        
        while queue:
            current_station, current_line, transfers = queue.popleft()
            
            # If we reached target, record the transfers
            if current_station == target:
                min_transfers_to_target = min(min_transfers_to_target, transfers)
                continue
            
            # Explore neighbors
            for neighbor in G.neighbors(current_station):
                edge_lines = G.edges[current_station, neighbor].get('lines', set())
                
                for edge_line in edge_lines:
                    # Calculate transfers needed
                    new_transfers = transfers
                    if edge_line != current_line:
                        new_transfers += 1  # Need to transfer to this line
                    
                    # Check if this is a better path to (neighbor, edge_line)
                    state_key = (neighbor, edge_line)
                    if state_key not in visited or visited[state_key] > new_transfers:
                        visited[state_key] = new_transfers
                        queue.append((neighbor, edge_line, new_transfers))
        
        return min_transfers_to_target if min_transfers_to_target != float('inf') else num_lines
    
    if nx.is_connected(G):
        # Get only transfer and terminal nodes
        relevant_nodes = [n for n in G.nodes() if G.nodes[n].get('is_transfer', False) or G.nodes[n].get('is_terminal', False)]
        
        print(f"\n  DEBUG δ calculation:")
        print(f"    Total nodes in FRI graph: {G.number_of_nodes()}")
        print(f"    Relevant nodes for δ: {len(relevant_nodes)}")
        print(f"    Graph connected: {nx.is_connected(G)}")
        
        # Check if nodes have lines
        nodes_without_lines = [n for n in relevant_nodes if not G.nodes[n].get('lines', set())]
        if nodes_without_lines:
            print(f"    WARNING: {len(nodes_without_lines)} nodes have no lines!")
        
        if len(relevant_nodes) > 1:
            # Find maximum transfers needed between any pair
            max_transfers = 0
            problematic_pairs = []
            
            for i, source in enumerate(relevant_nodes):
                for target in relevant_nodes[i+1:]:
                    transfers = count_min_transfers_bfs(G, source, target)
                    if transfers >= num_lines:  # Likely a fallback value
                        problematic_pairs.append((source, target, transfers))
                    max_transfers = max(max_transfers, transfers)
            
            
            if problematic_pairs:
                print(f"    WARNING: {len(problematic_pairs)} pairs returned fallback value (≥{num_lines})")
                print(f"    First few problematic pairs:")
                for src, tgt, trans in problematic_pairs[:3]:
                    src_name = G.nodes[src].get('name', f'Station {src}')
                    tgt_name = G.nodes[tgt].get('name', f'Station {tgt}')
                    src_lines = G.nodes[src].get('lines', set())
                    tgt_lines = G.nodes[tgt].get('lines', set())
                    print(f"      {src_name} (lines: {src_lines}) → {tgt_name} (lines: {tgt_lines}): {trans} transfers")
            
            delta = max_transfers
        else:
            delta = 0
    else:
        # If not connected, calculate δ on the largest connected component
        print(f"\n  WARNING: FRI graph is NOT CONNECTED!")
        print(f"    Number of connected components: {nx.number_connected_components(G)}")
        components = list(nx.connected_components(G))
        print(f"    Component sizes: {sorted([len(c) for c in components], reverse=True)}")
        
        # Show isolated stations
        for i, comp in enumerate(sorted(components, key=len)):
            if len(comp) <= 3:  # Show small components
                comp_names = [G.nodes[n].get('name', str(n))[:40] for n in comp]
                comp_lines = [G.nodes[n].get('lines', set()) for n in comp]
                print(f"    Isolated component {i+1} ({len(comp)} nodes): {comp_names}")
                print(f"       Lines: {comp_lines}")
        
        # Use the largest connected component (should contain all transfer stations)
        largest_component = max(components, key=len)
        G_main = G.subgraph(largest_component).copy()
        
        print(f"    Using largest component ({len(largest_component)} nodes) for δ calculation")
        
        # Calculate δ on the main component
        relevant_nodes = [n for n in G_main.nodes() if G_main.nodes[n].get('is_transfer', False) or G_main.nodes[n].get('is_terminal', False)]
        
        if len(relevant_nodes) > 1:
            max_transfers = 0
            for i, source in enumerate(relevant_nodes):
                for target in relevant_nodes[i+1:]:
                    transfers = count_min_transfers_bfs(G_main, source, target)
                    max_transfers = max(max_transfers, transfers)
            delta = max_transfers
        else:
            delta = 0
    
    # Directness: τ = n_L / δ (Derrible & Kennedy equation 11)
    tau = num_lines / delta if delta > 0 else 1.0
    
    # 3. Connectivity (ρ)
    # ρ = (v_c^t - e^m) / v^t  (Derrible & Kennedy equation 13)
    # where v_c^t = Σ(l - 1) · v_{i,l}  (sum of transfer possibilities)
    # 
    # Transfer possibilities: a station with l lines offers (l-1) transfer possibilities
    # - 2 lines → 1 possibility
    # - 3 lines → 2 possibilities
    # - 4 lines → 3 possibilities, etc.
    
    v_c_t = 0  # Sum of transfer possibilities
    for node in G.nodes():
        if G.nodes[node].get('is_transfer', False):
            # Count number of lines at this transfer
            station_id = node
            lines_at_station = topology['station_lines'].get(station_id, set())
            l = len(lines_at_station)
            # Transfer possibilities = (l - 1)
            v_c_t += (l - 1)
    
    # Connectivity formula
    if v_t > 0:
        rho = (v_c_t - e_m) / v_t
    else:
        rho = 0
    
    rho = max(0, rho)  # Ensure non-negative
    
    return {
        'sigma': sigma,
        'tau': tau,
        'rho': rho,
        'v': v,
        'v_t': v_t,
        'v_e': v_e,
        'e': e,
        'e_s': e_s,
        'e_m': e_m,
        'delta': delta,
        'A': A,
        'L': total_length
    }


def predict_boardings_per_capita(sigma, tau, rho):
    """
    Derrible & Kennedy regression model:
    Bpc = 44.963σ + 7.579τ + 92.316ρ + 102.947
    """
    return 44.963 * sigma + 7.579 * tau + 92.316 * rho + 102.947


def compute_fri_baseline(G, topology, total_length, num_lines):
    """Compute baseline FRI metrics (no disruption)"""
    print("\n" + "=" * 80)
    print("COMPUTING FRI BASELINE METRICS")
    print("=" * 80)
    
    indicators = compute_derrible_kennedy_indicators(G, topology, total_length, num_lines)
    bpc = predict_boardings_per_capita(indicators['sigma'], indicators['tau'], indicators['rho'])
    
    print(f"\nNetwork Statistics:")
    print(f"  Total vertices (v): {indicators['v']}")
    print(f"  Transfer vertices (v_t): {indicators['v_t']}")
    print(f"  Terminal vertices (v_e): {indicators['v_e']}")
    print(f"  Total edges (e): {indicators['e']}")
    print(f"  Single-use edges (e_s): {indicators['e_s']}")
    print(f"  Multiple-use edges (e_m): {indicators['e_m']}")
    
    print(f"\nDerrible & Kennedy Indicators:")
    print(f"  Coverage (σ): {indicators['sigma']:.4f}")
    print(f"  Directness (τ): {indicators['tau']:.4f}")
    print(f"    - Max transfers (δ): {indicators['delta']}")
    print(f"    - Number of lines: {num_lines}")
    print(f"  Connectivity (ρ): {indicators['rho']:.4f}")
    
    print(f"\nPredicted Performance:")
    print(f"  Boardings per capita: {bpc:.2f}")
    
    return indicators, bpc


def simulate_disruption_scenario(G_original, topology, stations_df, failed_stations):
    """
    Simulate a disruption scenario by removing failed stations
    Returns new graph and recomputed indicators
    """
    G = G_original.copy()
    
    # Remove failed stations
    G.remove_nodes_from(failed_stations)
    
    # Recompute topology for remaining network
    remaining_stations = set(G.nodes())
    
    # Update transfer and terminal counts
    new_topology = topology.copy()
    new_topology['transfer_stations'] = topology['transfer_stations'] - failed_stations
    new_topology['terminal_stations'] = topology['terminal_stations'] - failed_stations
    
    # Recalculate route length (sum of remaining edges)
    new_length = 0
    for edge in G.edges():
        s1, s2 = edge
        lat1 = stations_df[stations_df['station_id'] == s1]['lat'].values[0]
        lon1 = stations_df[stations_df['station_id'] == s1]['lon'].values[0]
        lat2 = stations_df[stations_df['station_id'] == s2]['lat'].values[0]
        lon2 = stations_df[stations_df['station_id'] == s2]['lon'].values[0]
        new_length += haversine_distance(lat1, lon1, lat2, lon2)
    
    return G, new_topology, new_length


def compute_fri(G_baseline, G_full, topology, stations_df, total_length, num_lines, baseline_bpc):
    """
    Compute FRI (Functional Resilience Index) across multiple disruption scenarios
    """
    print("\n" + "=" * 80)
    print("COMPUTING FRI ACROSS DISRUPTION SCENARIOS")
    print("=" * 80)
    
    scenarios = []
    failed_stations_log = []  # Track which stations were removed in each scenario
    
    all_stations = list(G_baseline.nodes())
    
    # 1. Random failures
    print("\n1. Random Station Failures")
    for prob in RANDOM_FAILURE_PROBS:
        for run in range(RANDOM_SCENARIOS_PER_PROB):
            # Randomly select stations to fail
            num_fail = int(len(all_stations) * prob)
            if num_fail == 0:
                continue
            
            failed = set(np.random.choice(all_stations, size=num_fail, replace=False))
            
            G_disrupted, new_topology, new_length = simulate_disruption_scenario(
                G_baseline, topology, stations_df, failed
            )
            
            if G_disrupted.number_of_nodes() > 0:
                indicators = compute_derrible_kennedy_indicators(
                    G_disrupted, new_topology, new_length, num_lines
                )
                bpc = predict_boardings_per_capita(indicators['sigma'], indicators['tau'], indicators['rho'])
                performance_ratio = bpc / baseline_bpc if baseline_bpc > 0 else 0
                
                # Count isolated stations (in components other than largest)
                if not nx.is_connected(G_disrupted):
                    components = list(nx.connected_components(G_disrupted))
                    largest_size = max(len(c) for c in components)
                    isolated_count = sum(len(c) for c in components if len(c) < largest_size)
                else:
                    isolated_count = 0
                
                # Calculate % of station pairs still reachable (better degradation metric)
                # This DECREASES as network fragments (unlike avg path which can be misleading)
                remaining = set(G_full.nodes()) - failed
                G_full_disrupted = G_full.subgraph(remaining).copy()
                
                reachable_pct = 0
                if G_full_disrupted.number_of_nodes() > 1:
                    # Count reachable pairs in each component
                    if nx.is_connected(G_full_disrupted):
                        # All pairs are reachable
                        n = G_full_disrupted.number_of_nodes()
                        reachable_pairs = n * (n - 1) / 2
                    else:
                        # Only pairs within same component are reachable
                        reachable_pairs = 0
                        components = list(nx.connected_components(G_full_disrupted))
                        for comp in components:
                            n = len(comp)
                            if n > 1:
                                reachable_pairs += n * (n - 1) / 2
                    
                    # Calculate as % of original network (170 stations = 14,365 pairs)
                    total_original_pairs = 170 * 169 / 2
                    reachable_pct = (reachable_pairs / total_original_pairs) * 100
            else:
                performance_ratio = 0
                isolated_count = len(all_stations)
                reachable_pct = 0
            
            scenarios.append({
                'type': 'random',
                'prob': prob,
                'run': run,
                'failed_count': len(failed),
                'performance_ratio': performance_ratio,
                'isolated_stations': isolated_count,
                'reachable_pct': reachable_pct
            })
            
            # Log failed stations
            failed_names = [G_baseline.nodes[sid].get('name', str(sid)) for sid in failed]
            failed_stations_log.append({
                'scenario_type': 'random',
                'failure_prob': prob,
                'run': run,
                'failed_count': len(failed),
                'failed_stations': '; '.join(sorted(failed_names))
            })
    
    # 2. Targeted failures by degree
    print("2. Targeted Failures (by degree)")
    for k in TARGETED_FAILURE_COUNTS:
        if k >= len(all_stations):
            continue
        
        # Sort stations by degree
        degrees = dict(G_baseline.degree())
        top_k = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:k]
        failed = set([s[0] for s in top_k])
        
        G_disrupted, new_topology, new_length = simulate_disruption_scenario(
            G_baseline, topology, stations_df, failed
        )
        
        if G_disrupted.number_of_nodes() > 0:
            indicators = compute_derrible_kennedy_indicators(
                G_disrupted, new_topology, new_length, num_lines
            )
            bpc = predict_boardings_per_capita(indicators['sigma'], indicators['tau'], indicators['rho'])
            performance_ratio = bpc / baseline_bpc if baseline_bpc > 0 else 0
            
            # Count isolated stations
            if not nx.is_connected(G_disrupted):
                components = list(nx.connected_components(G_disrupted))
                largest_size = max(len(c) for c in components)
                isolated_count = sum(len(c) for c in components if len(c) < largest_size)
            else:
                isolated_count = 0
            
            # Calculate % reachable pairs
            remaining = set(G_full.nodes()) - failed
            G_full_disrupted = G_full.subgraph(remaining).copy()
            reachable_pct = 0
            if G_full_disrupted.number_of_nodes() > 1:
                if nx.is_connected(G_full_disrupted):
                    n = G_full_disrupted.number_of_nodes()
                    reachable_pairs = n * (n - 1) / 2
                else:
                    reachable_pairs = 0
                    components = list(nx.connected_components(G_full_disrupted))
                    for comp in components:
                        n = len(comp)
                        if n > 1:
                            reachable_pairs += n * (n - 1) / 2
                total_original_pairs = 170 * 169 / 2
                reachable_pct = (reachable_pairs / total_original_pairs) * 100
        else:
            performance_ratio = 0
            isolated_count = k
            reachable_pct = 0
        
        scenarios.append({
            'type': 'degree',
            'failed_count': k,
            'performance_ratio': performance_ratio,
            'isolated_stations': isolated_count,
            'reachable_pct': reachable_pct
        })
        
        # Log failed stations
        failed_names = [G_baseline.nodes[sid].get('name', str(sid)) for sid in failed]
        failed_stations_log.append({
            'scenario_type': 'degree',
            'failure_prob': None,
            'run': None,
            'failed_count': k,
            'failed_stations': '; '.join(sorted(failed_names))
        })
    
    # 3. Targeted failures by betweenness centrality
    print("3. Targeted Failures (by betweenness)")
    if nx.is_connected(G_baseline):
        betweenness = nx.betweenness_centrality(G_baseline)
        
        for k in TARGETED_FAILURE_COUNTS:
            if k >= len(all_stations):
                continue
            
            top_k = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:k]
            failed = set([s[0] for s in top_k])
            
            G_disrupted, new_topology, new_length = simulate_disruption_scenario(
                G_baseline, topology, stations_df, failed
            )
            
            if G_disrupted.number_of_nodes() > 0:
                indicators = compute_derrible_kennedy_indicators(
                    G_disrupted, new_topology, new_length, num_lines
                )
                bpc = predict_boardings_per_capita(indicators['sigma'], indicators['tau'], indicators['rho'])
                performance_ratio = bpc / baseline_bpc if baseline_bpc > 0 else 0
                
                # Count isolated stations
                if not nx.is_connected(G_disrupted):
                    components = list(nx.connected_components(G_disrupted))
                    largest_size = max(len(c) for c in components)
                    isolated_count = sum(len(c) for c in components if len(c) < largest_size)
                else:
                    isolated_count = 0
                
                # Calculate % reachable pairs
                remaining = set(G_full.nodes()) - failed
                G_full_disrupted = G_full.subgraph(remaining).copy()
                reachable_pct = 0
                if G_full_disrupted.number_of_nodes() > 1:
                    if nx.is_connected(G_full_disrupted):
                        n = G_full_disrupted.number_of_nodes()
                        reachable_pairs = n * (n - 1) / 2
                    else:
                        reachable_pairs = 0
                        components = list(nx.connected_components(G_full_disrupted))
                        for comp in components:
                            n = len(comp)
                            if n > 1:
                                reachable_pairs += n * (n - 1) / 2
                    total_original_pairs = 170 * 169 / 2
                    reachable_pct = (reachable_pairs / total_original_pairs) * 100
            else:
                performance_ratio = 0
                isolated_count = k
                reachable_pct = 0
            
            scenarios.append({
                'type': 'betweenness',
                'failed_count': k,
                'performance_ratio': performance_ratio,
                'isolated_stations': isolated_count,
                'reachable_pct': reachable_pct
            })
            
            # Log failed stations
            failed_names = [G_baseline.nodes[sid].get('name', str(sid)) for sid in failed]
            failed_stations_log.append({
                'scenario_type': 'betweenness',
                'failure_prob': None,
                'run': None,
                'failed_count': k,
                'failed_stations': '; '.join(sorted(failed_names))
            })
    
    # Calculate FRI for each scenario type
    scenarios_df = pd.DataFrame(scenarios)
    
    # Overall FRI
    fri_overall = scenarios_df['performance_ratio'].mean()
    
    # FRI by type
    fri_by_type = scenarios_df.groupby('type')['performance_ratio'].mean()
    
    print(f"\n{'Type':<20} {'FRI':<10}")
    print("-" * 30)
    for scenario_type, fri_value in fri_by_type.items():
        print(f"{scenario_type:<20} {fri_value:.4f}")
    print("-" * 30)
    print(f"{'Overall':<20} {fri_overall:.4f}")
    
    return fri_overall, fri_by_type, scenarios_df, pd.DataFrame(failed_stations_log)


# ==================================================================================
# SME (SYSTEM LEVEL MOBILITY EFFICIENCY) CALCULATIONS
# ==================================================================================

def compute_reachability(G, time_threshold_minutes):
    """
    For each station, compute which other stations are reachable within the time threshold
    Returns dictionary: station_id -> set of reachable station_ids
    """
    reachability = {}
    
    for source in G.nodes():
        # Dijkstra's algorithm with time threshold
        lengths = nx.single_source_dijkstra_path_length(
            G, source, cutoff=time_threshold_minutes, weight='travel_time'
        )
        reachability[source] = set(lengths.keys())
    
    return reachability


def estimate_reachable_area(stations_df, reachable_station_ids):
    """
    Estimate area reachable from a set of stations
    Using convex hull area as approximation
    """
    if len(reachable_station_ids) < 3:
        return 0
    
    from scipy.spatial import ConvexHull
    
    # Get coordinates of reachable stations
    coords = []
    for sid in reachable_station_ids:
        station = stations_df[stations_df['station_id'] == sid]
        if len(station) > 0:
            lat = station.iloc[0]['lat']
            lon = station.iloc[0]['lon']
            coords.append([lon, lat])
    
    if len(coords) < 3:
        return 0
    
    try:
        # Calculate convex hull
        hull = ConvexHull(coords)
        
        # Convert to km² (approximate - this is in degrees²)
        # Rough conversion at Berlin latitude (52.5°)
        deg_to_km_lat = 111.0
        deg_to_km_lon = 111.0 * np.cos(np.radians(52.5))
        
        area_deg2 = hull.volume  # In 2D, volume is area
        area_km2 = area_deg2 * deg_to_km_lat * deg_to_km_lon
        
        return area_km2
    except:
        return 0


def compute_sme(G_full, stations_df, total_length):
    """
    Compute SME (System Level Mobility Efficiency) for different time thresholds
    """
    print("\n" + "=" * 80)
    print("COMPUTING SME (SYSTEM LEVEL MOBILITY EFFICIENCY)")
    print("=" * 80)
    
    # Try to import scipy for convex hull
    try:
        from scipy.spatial import ConvexHull
        HAS_SCIPY = True
    except ImportError:
        HAS_SCIPY = False
        print("\nWarning: scipy not available, SME will be approximate")
    
    sme_results = []
    
    for time_threshold in SME_TIME_THRESHOLDS:
        print(f"\nTime threshold: {time_threshold} minutes")
        
        # Compute reachability
        reachability = compute_reachability(G_full, time_threshold)
        
        # Calculate average reachability per station
        total_reachable_count = 0
        max_travel_time = 0
        reachability_counts = []
        
        for source in G_full.nodes():
            reachable_from_source = reachability.get(source, set())
            reachability_counts.append(len(reachable_from_source))
            total_reachable_count += len(reachable_from_source)
            
            # Check actual max travel time
            for target in G_full.nodes():
                try:
                    travel_time = nx.shortest_path_length(G_full, source, target, weight='travel_time')
                    max_travel_time = max(max_travel_time, travel_time)
                except:
                    pass
       
        avg_reachable_per_station = total_reachable_count / len(G_full.nodes()) if len(G_full.nodes()) > 0 else 0
        reachability_pct = (total_reachable_count / (len(G_full.nodes()) ** 2) * 100) if len(G_full.nodes()) > 0 else 0
        
        # Get stations that are reachable from the average station
        # Use the median number of reachable stations as representative
        median_reachable = sorted(reachability_counts)[len(reachability_counts) // 2] if reachability_counts else 0
        
        # Estimate reachable area based on average reachability
        # Use stations from a representative "average" station
        if HAS_SCIPY and avg_reachable_per_station > 2:
            # Pick a station with close to average reachability
            representative_station = min(G_full.nodes(), 
                                        key=lambda s: abs(len(reachability.get(s, set())) - avg_reachable_per_station))
            representative_reachable = reachability.get(representative_station, set())
            reachable_area = estimate_reachable_area(stations_df, representative_reachable)
        else:
            # Fallback: use average reachable stations as proxy
            reachable_area = avg_reachable_per_station * 2  # Assume 2 km² per station
        
        # SME (area-based)
        # SME = Reachable area / (Track length / Population)
        sme = reachable_area / (total_length / SINGAPORE_POPULATION * 1000)  # Normalize
        
        print(f"  Average reachable stations: {avg_reachable_per_station:.1f} / {len(stations_df)} ({reachability_pct:.1f}%)")
        print(f"  Median reachable: {median_reachable}")
        print(f"  Max travel time in network: {max_travel_time:.1f} min")
        print(f"  Estimated reachable area: {reachable_area:.2f} km²")
        print(f"  SME: {sme:.2f}")
        
        sme_results.append({
            'time_threshold': time_threshold,
            'avg_reachable_stations': avg_reachable_per_station,
            'median_reachable': median_reachable,
            'reachability_pct': reachability_pct,
            'max_travel_time': max_travel_time,
            'reachable_area_km2': reachable_area,
            'sme': sme
        })
    
    return pd.DataFrame(sme_results)


# ==================================================================================
# MAIN EXECUTION
# ==================================================================================



# ==================================================================================
# VISUALIZATION FUNCTIONS
# ==================================================================================

def visualize_network_graph(G, stations_df, topology, output_path):
    """Visualize the D&K simplified network graph with 3 different layouts"""
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available, skipping network visualization")
        return
    
    import matplotlib.pyplot as plt
    
    # Get GPS coordinates
    gps_pos = {}
    for node in G.nodes():
        station_data = stations_df[stations_df['station_id'] == node]
        if len(station_data) > 0:
            gps_pos[node] = (station_data['lon'].values[0], station_data['lat'].values[0])
    
    # Create 3 different layouts
    layouts = {
        'geographic': gps_pos,
        'kamada_kawai': nx.kamada_kawai_layout(G, scale=2),
        'hierarchical': nx.spring_layout(G, k=1.5, iterations=100, seed=42)
    }
    
    layout_titles = {
        'geographic': 'Geographic Layout (GPS Coordinates)',
        'kamada_kawai': 'Kamada-Kawai Layout (Force-Directed)',
        'hierarchical': 'Spring Layout (Optimized Spacing)'
    }
    
    # Generate each layout version
    for layout_name, pos in layouts.items():
        fig, ax = plt.subplots(1, 1, figsize=(20, 16))
        
        # Node colors and sizes
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            if G.nodes[node].get('is_transfer', False):
                node_colors.append('#E63946')
                node_sizes.append(500)
            else:
                node_colors.append('#06D6A0')
                node_sizes.append(300)
        
        # Edge styling
        edge_colors = []
        edge_widths = []
        for edge in G.edges():
            lines = G.edges[edge].get('lines', set())
            if len(lines) > 1:
                edge_colors.append('#FFB703')
                edge_widths.append(3.0)
            else:
                edge_colors.append('#8ECAE6')
                edge_widths.append(1.5)
        
        # Draw network
        nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, 
                              alpha=0.4, ax=ax)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                              alpha=0.95, ax=ax, edgecolors='white', linewidths=2.5)
        
        # Label major transfer stations
        degrees = dict(G.degree())
        transfer_nodes = [n for n in G.nodes() if G.nodes[n].get('is_transfer', False)]
        top_transfers = sorted(transfer_nodes, key=lambda n: degrees.get(n, 0), reverse=True)[:12]
        
        for node in top_transfers:
            name = G.nodes[node].get('name', '')
            name = name.replace('Bstggl.1', '').replace('Bstggl.2', '')
            name = name.replace('S+U ', '').replace('U ', '').strip()
            
            x, y = pos[node]
            
            # Adjust offset based on layout
            if layout_name == 'geographic':
                offset_x = 0.003 if x > 13.4 else -0.003
                offset_y = 0.003 if y > 52.52 else -0.003
            else:
                offset_x = 0.08 if x > 0 else -0.08
                offset_y = 0.08 if y > 0 else -0.08
            
            ax.text(x + offset_x, y + offset_y, name[:18], 
                   fontsize=10, fontweight='bold',
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                            edgecolor='gray', alpha=0.9, linewidth=0.5),
                   zorder=1000)
        
        # Title
        ax.set_title(f'Berlin U-Bahn Network — {layout_titles[layout_name]}\n' + 
                    f'{G.number_of_nodes()} Vertices · {G.number_of_edges()} Edges · ' +
                    f'27 Transfer · 14 Terminal Stations',
                    fontsize=20, fontweight='bold', pad=30, color='#1A1A1D')
        
        # For geographic layout, set tight bounds to remove extra whitespace
        if layout_name == 'geographic':
            x_coords = [pos[n][0] for n in G.nodes()]
            y_coords = [pos[n][1] for n in G.nodes()]
            
            # Set tight limits with minimal padding
            x_padding = (max(x_coords) - min(x_coords)) * 0.02
            y_padding = (max(y_coords) - min(y_coords)) * 0.02
            
            ax.set_xlim(min(x_coords) - x_padding, max(x_coords) + x_padding)
            ax.set_ylim(min(y_coords) - y_padding, max(y_coords) + y_padding)
            ax.margins(0)
        
        ax.axis('off')
        
        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#E63946', 
                  markersize=14, label='Transfer Station', markeredgecolor='white', markeredgewidth=2),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#06D6A0', 
                  markersize=11, label='Terminal Station', markeredgecolor='white', markeredgewidth=2),
            Line2D([0], [0], color='#FFB703', linewidth=3.5, label='Multiple-use Edge'),
            Line2D([0], [0], color='#8ECAE6', linewidth=2.5, label='Single-use Edge')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=13, 
                 frameon=True, fancybox=True, shadow=True, framealpha=0.95)
        
        ax.set_facecolor('#F8F9FA')
        
        # Tight layout with minimal padding
        plt.tight_layout(pad=0.5)
        
        # Save with layout-specific filename
        base_path = output_path.replace('.png', '')
        layout_path = f"{base_path}_{layout_name}.png"
        plt.savefig(layout_path, dpi=300, bbox_inches='tight', pad_inches=0.1, facecolor='white')
        plt.close()
        print(f"  Saved {layout_name} layout to {layout_path}")


def visualize_fri_resilience(scenarios_df, output_path):
    """Visualize FRI resilience curves for different disruption scenarios"""
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available, skipping FRI visualization")
        return
    
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Random failures
    random_data = scenarios_df[scenarios_df['type'] == 'random'].copy()
    if len(random_data) > 0:
        grouped = random_data.groupby('prob')['performance_ratio'].agg(['mean', 'std'])
        ax1.errorbar(grouped.index * 100, grouped['mean'], yerr=grouped['std'], 
                    marker='o', linewidth=2, markersize=8, capsize=5, 
                    color='#FF6B6B', label='Mean ± Std')
        ax1.fill_between(grouped.index * 100, grouped['mean'] - grouped['std'], 
                        grouped['mean'] + grouped['std'], alpha=0.2, color='#FF6B6B')
        ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Baseline')
        ax1.set_xlabel('Failure Probability (%)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Performance Ratio', fontsize=12, fontweight='bold')
        ax1.set_title('Random Station Failures', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        ax1.set_ylim([0.8, 1.05])
    
    # Plot 2: Targeted failures
    for scenario_type in ['degree', 'betweenness']:
        targeted_data = scenarios_df[scenarios_df['type'] == scenario_type].copy()
        if len(targeted_data) > 0:
            grouped = targeted_data.groupby('failed_count')['performance_ratio'].mean()
            color = '#4ECDC4' if scenario_type == 'degree' else '#FFD93D'
            ax2.plot(grouped.index, grouped.values, marker='o', linewidth=2, 
                    markersize=8, label=scenario_type.capitalize(), color=color)
    
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Baseline')
    ax2.set_xlabel('Number of Stations Removed', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Performance Ratio', fontsize=12, fontweight='bold')
    ax2.set_title('Targeted Station Failures', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_ylim([0.8, 1.05])
    
    plt.suptitle('Functional Resilience Index (FRI) - Network Performance Under Disruptions',
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved FRI resilience curves to {output_path}")


def visualize_sme_analysis(sme_df, output_path):
    """Visualize SME reachability analysis"""
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available, skipping SME visualization")
        return
    
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Reachability vs Time
    time_thresholds = sme_df['time_threshold'].values
    reachability_pct = sme_df['reachability_pct'].values
    avg_reachable = sme_df['avg_reachable_stations'].values
    
    color = '#4ECDC4'
    ax1.plot(time_thresholds, reachability_pct, marker='o', linewidth=3, 
            markersize=10, color=color, label='Reachability %')
    ax1.fill_between(time_thresholds, 0, reachability_pct, alpha=0.3, color=color)
    
    # Add value labels
    for x, y in zip(time_thresholds, reachability_pct):
        ax1.text(x, y + 3, f'{y:.1f}%', ha='center', fontsize=10, fontweight='bold')
    
    ax1.set_xlabel('Time Threshold (minutes)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Stations Reachable (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Network Reachability vs Travel Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 105])
    ax1.set_xticks(time_thresholds)
    
    # Plot 2: SME values
    sme_values = sme_df['sme'].values
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(time_thresholds)))
    bars = ax2.bar(range(len(time_thresholds)), sme_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, sme_values)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'{val:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('Time Threshold (minutes)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('SME Value', fontsize=12, fontweight='bold')
    ax2.set_title('System Level Mobility Efficiency (SME)', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(time_thresholds)))
    ax2.set_xticklabels([f'{t} min' for t in time_thresholds])
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('SME Analysis - Network Accessibility and Mobility Efficiency',
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved SME analysis to {output_path}")


def visualize_network_degradation(scenarios_df, output_path):
    """Visualize network degradation metrics: isolated stations and travel time"""
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available, skipping degradation visualization")
        return
    
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Isolated Stations
    for scenario_type in ['degree', 'betweenness']:
        targeted_data = scenarios_df[scenarios_df['type'] == scenario_type].copy()
        if len(targeted_data) > 0 and 'isolated_stations' in targeted_data.columns:
            grouped = targeted_data.groupby('failed_count')['isolated_stations'].mean()
            color = '#E63946' if scenario_type == 'degree' else '#FFB703'
            ax1.plot(grouped.index, grouped.values, marker='o', linewidth=2.5, 
                    markersize=8, label=scenario_type.capitalize(), color=color)
            ax1.fill_between(grouped.index, 0, grouped.values, alpha=0.2, color=color)
    
    ax1.set_xlabel('Number of Stations Removed', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Isolated Stations (Count)', fontsize=12, fontweight='bold')
    ax1.set_title('Network Fragmentation\nStations Isolated from Main Network', 
                 fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_ylim(bottom=0)
    
    # Plot 2: Network Connectivity (% Reachable Pairs)
    for scenario_type in ['degree', 'betweenness']:
        targeted_data = scenarios_df[scenarios_df['type'] == scenario_type].copy()
        if len(targeted_data) > 0 and 'reachable_pct' in targeted_data.columns:
            grouped = targeted_data.groupby('failed_count')['reachable_pct'].mean()
            color = '#06D6A0' if scenario_type == 'degree' else '#8ECAE6'
            ax2.plot(grouped.index, grouped.values, marker='s', linewidth=2.5, 
                    markersize=8, label=scenario_type.capitalize(), color=color)
            ax2.fill_between(grouped.index, grouped.values, 100, alpha=0.2, color=color)
    
    ax2.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Baseline (100%)')
    ax2.set_xlabel('Number of Stations Removed', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Reachable Pairs (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Network Connectivity Degradation\nStation Pairs Still Reachable', 
                 fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_ylim(bottom=0)
    
    plt.suptitle('Network Degradation Analysis — Impact of Station Failures',
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved network degradation analysis to {output_path}")


# ==================================================================================
# MAIN ANALYSIS
# ==================================================================================

import datetime # Added for datetime.now()

def main():
    """Run complete network analysis"""
    print("\n" + "=" * 80)
    print("SINGAPORE MRT/LRT NETWORK ANALYSIS")
    print("FRI & SME Metrics Implementation")
    print("=" * 80)
    print(f"Start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    routes, trips, stop_times, stops = load_singapore_data()
    
    # Identify unique stations
    stations_df, stop_to_station = identify_unique_stations(stops)
    
    # Calculate travel times
    avg_travel_times = calculate_travel_times(stop_times, trips)
    
    # Build network topology
    topology = build_network_topology(routes, trips, stop_times, stations_df, stop_to_station, avg_travel_times)
    
    # Create graphs
    print("\n" + "-" * 80)
    print("Creating network graphs...")
    G_fri = create_networkx_graph(stations_df, topology, stop_to_station, avg_travel_times, for_fri=True)
    G_full = create_networkx_graph(stations_df, topology, stop_to_station, avg_travel_times, for_fri=False)
    print(f"FRI graph: {G_fri.number_of_nodes()} nodes, {G_fri.number_of_edges()} edges")
    print(f"Full graph: {G_full.number_of_nodes()} nodes, {G_full.number_of_edges()} edges")
    
    # === FRI ANALYSIS ===
    baseline_indicators, baseline_bpc = compute_fri_baseline(
        G_fri, topology, topology['total_length'], topology['num_lines']
    )
    
    fri_overall, fri_by_type, scenarios_df, failed_stations_df = compute_fri(
        G_fri, G_full, topology, stations_df, topology['total_length'],
        topology['num_lines'], baseline_bpc
    )
    
    # Save FRI results
    baseline_df = pd.DataFrame([baseline_indicators])
    baseline_df['baseline_bpc'] = baseline_bpc
    baseline_df.to_csv(os.path.join(OUTPUT_DIR, 'fri_baseline_metrics.csv'), index=False)
    scenarios_df.to_csv(os.path.join(OUTPUT_DIR, 'fri_scenarios.csv'), index=False)
    failed_stations_df.to_csv(os.path.join(OUTPUT_DIR, 'fri_failed_stations.csv'), index=False)
    print(f"\nSaved FRI results to fri_baseline_metrics.csv, fri_scenarios.csv, and fri_failed_stations.csv")
    
    # === SME ANALYSIS ===
    sme_df = compute_sme(G_full, stations_df, topology['total_length'])
    sme_df.to_csv(os.path.join(OUTPUT_DIR, 'sme_results.csv'), index=False)
    print(f"\nSaved SME results to sme_results.csv")
    
    # === SUMMARY ===
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nNetwork Statistics:")
    print(f"  Total stations: {len(stations_df)}")
    print(f"  Transfer stations: {len(topology['transfer_stations'])}")
    print(f"  Terminal stations: {len(topology['terminal_stations'])}")
    print(f"  Total lines: {topology['num_lines']}")
    print(f"  Total route length: {topology['total_length']:.2f} km")
    
    print(f"\nFRI (Functional Resilience Index):")
    print(f"  Overall FRI: {fri_overall:.4f}")
    for scenario_type, fri_value in fri_by_type.items():
        print(f"  FRI ({scenario_type}): {fri_value:.4f}")
    
    print(f"\nSME (System Level Mobility Efficiency):")
    for _, row in sme_df.iterrows():
        print(f"  SME @ {row['time_threshold']} min: {row['sme']:.2f}")
    
    # === VISUALIZATIONS ===
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)
    
    visualize_network_graph(G_fri, stations_df, topology, 
                           os.path.join(OUTPUT_DIR, 'network_graph.png'))
    visualize_fri_resilience(scenarios_df, 
                           os.path.join(OUTPUT_DIR, 'fri_resilience_curves.png'))
    visualize_sme_analysis(sme_df, 
                          os.path.join(OUTPUT_DIR, 'sme_analysis.png'))
    visualize_network_degradation(scenarios_df,
                                  os.path.join(OUTPUT_DIR, 'network_degradation.png'))
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
