# Metro Network Resilience Analysis - Methodology Report

## Project Overview

This report documents the implementation of Derrible & Kennedy (2009) network topology metrics and Functional Resilience Index (FRI) analysis for metro transit systems in New York City, Berlin, Singapore (current), and Singapore (2009).

## 1. Data Sources & Processing

### GTFS Data
- **NYC**: MTA GTFS feed (excludes Staten Island Railway)
- **Berlin**: VBB GTFS feed (U-Bahn and S-Bahn)
- **Singapore**: LTA DataMall GTFS feed
- **Singapore 2009**: Historical GTFS data for validation

### Key Processing Steps
1. Filter routes by `route_type == 1` (metro/subway systems)
2. Extract stations, stop times, and route geometries
3. Calculate inter-station travel times from stop_times data
4. Build network topology following D&K methodology

## 2. Network Topology (Derrible & Kennedy Model)

### Simplified Graph Construction
Following D&K (2009), we create a simplified graph G = (V, E) where:
- **V** = Transfer stations (v^t) ∪ Terminal stations (v^e)
- **E** = Direct connections between special vertices

### Station Classification
```python
# Transfer Stations (v^t): Serve multiple lines
transfer_stations = stations with len(lines) >= 2

# Terminal Stations (v^e): End points of lines
terminal_stations = first and last stops of each line
```

### Edge Classification
```python
# Single-use edges (e^s): Used by one line
# Multiple-use edges (e^m): Shared by multiple lines
```

## 3. Derrible & Kennedy Indicators

### Implementation Details

#### Delta (δ) - Maximum Transfers
**Definition Ambiguity**: The D&K paper uses "maximum number of transfers" but doesn't specify whether this means:
- δ_transfers: Number of line changes
- δ_trains: Number of trains boarded (line changes + 1)

**Dual Implementation**: We calculate both interpretations:

```python
def count_min_transfers_bfs(G, source, target, topology):
    """
    BFS that tracks LINE changes, not just hops.
    Returns: (transfers, trains_boarded)
    where trains_boarded = transfers + 1
    """
    # Implementation tracks which lines serve each edge
    # Counts transfers when forced to switch lines
```

**Calculated Metrics**:
- `delta_transfers`: Maximum line changes needed
- `delta_trains`: Maximum trains boarded (delta_transfers + 1)
- `tau_by_transfers`: n_L / delta_transfers
- `tau_by_trains`: n_L / delta_trains

#### Other Topology Metrics

**Sigma (σ) - Network Dimension**
```python
sigma = (num_lines + num_stations) / (2 * num_transfer_stations)
```

**Rho (ρ) - Network Connectivity**
```python
rho = (num_edges - num_stations + 1) / ((2 * num_stations) - (5 * sqrt(num_stations)) + 2)
```

**Eta (η) - Directness vs. Indirectness Ratio**
```python
# Count parallel vs. diverging edges at transfer stations
eta = diverging_edges / parallel_edges if parallel_edges > 0 else float('inf')
```

## 4. System-Level Mobility Efficiency (SME)

### Formula
```python
SME = A_T / (L · Pop_millions)
```

Where:
- **A_T**: Reachable area within time threshold (km²)
- **L**: Total track length (km)
- **Pop_millions**: Metropolitan population in millions

### Area Estimation Methods

**1. ConvexHull (when scipy available)**:
```python
from scipy.spatial import ConvexHull
points = [(lat, lon) for reachable stations]
hull = ConvexHull(points)
area = hull.volume * (111.32)^2  # Convert to km²
```

**2. Fallback Method**:
```python
area = num_reachable_stations * 2  # Assume 2 km² per station
```

### Time Thresholds
Analysis performed for multiple thresholds: 15, 30, 45, 60 minutes

## 5. Functional Resilience Index (FRI)

### Dual FRI Implementation

To address delta ambiguity, we calculate FRI using **both** interpretations:

#### Performance Ratio Calculation
```python
# Baseline
baseline_bpc = predict_boardings_per_capita(baseline_sigma, baseline_tau, baseline_rho)

# For each disruption scenario:
bpc_by_transfers = predict_boardings_per_capita(sigma, tau_by_transfers, rho)
bpc_by_trains = predict_boardings_per_capita(sigma, tau_by_trains, rho)

performance_ratio_by_transfers = bpc_by_transfers / baseline_bpc
performance_ratio_by_trains = bpc_by_trains / baseline_bpc
```

#### Fragmentation Penalty (NYC, Berlin, Singapore)
```python
fragmentation_penalty = remaining_nodes / baseline_nodes
performance_ratio *= fragmentation_penalty
```

### Disruption Scenarios

#### 1. Random Station Failures
- Probabilities: 1%, 2%, 3%, 4%, 5%
- Runs: 10 per probability
- Metric: Mean ± Std of performance ratio

#### 2. Degree-Based Targeted Failures
- Remove top-k highest degree stations
- k = 1 to 10
- Sequential removal by degree centrality

#### 3. Betweenness-Based Targeted Failures
- Remove top-k highest betweenness stations
- k = 1 to 10
- Sequential removal by betweenness centrality

### FRI Calculation
```python
# Overall FRI (using trains interpretation as default)
fri_overall = mean(all performance_ratio_by_trains)

# Per-scenario FRI
fri_random = mean(random scenario performance_ratios)
fri_degree = mean(degree scenario performance_ratios)
fri_betweenness = mean(betweenness scenario performance_ratios)
```

## 6. Visualization Outputs

### Network Graphs
- **Geographic**: GPS coordinates layout
- **Kamada-Kawai**: Force-directed layout
- **Hierarchical**: Spring layout for visual clarity

### Dual FRI Resilience Plots

Each city generates **two FRI plots**:

**1. fri_transfers_{city}.png**
- Uses τ = n_L / δ_transfers (line changes)
- Shows FRI degradation based on transfer count interpretation

**2. fri_trains_{city}.png**
- Uses τ = n_L / δ_trains (trains boarded)
- Shows FRI degradation based on trains boarded interpretation

**Plot Components**:
- Left subplot: Random failures (failure % vs performance ratio)
- Right subplot: Targeted failures (stations removed vs performance ratio)

### Other Visualizations
- **SME Analysis**: Reachability vs time thresholds
- **Network Degradation**: Isolated stations and connectivity loss

## 7. Constants & Parameters

### City-Specific Constants

```python
# NYC
NYC_AREA_KM2 = 629.2  # Excluding Staten Island
NYC_POPULATION = 8_336_817

# Berlin
BERLIN_AREA_KM2 = 891.8
BERLIN_POPULATION = 3_644_826

# Singapore
SINGAPORE_AREA_KM2 = 733.1
SINGAPORE_POPULATION = 5_453_600
```

## 8. Key Implementation Decisions

### Delta Interpretation
**Decision**: Calculate and visualize both interpretations
**Rationale**: D&K paper ambiguity requires empirical comparison to determine which matches their reported values

### SME Standardization
**Formula Used**: `SME = A_T / (L · Pop_millions)`
**Previous Issues**: NYC and Singapore 2009 initially used different normalization
**Resolution**: Standardized across all 4 scripts

### Graph Selection for Delta
**Decision**: Use simplified D&K graph for delta calculation
**Rationale**: 
- Consistent with D&K methodology
- Full graph yields same results for NYC
- Proper representation of line-based transfers

## 9. Output File Naming Convention

```
ng_{city}.png                  # Network graph
fri_transfers_{city}.png       # FRI using δ_transfers
fri_trains_{city}.png          # FRI using δ_trains
sme_{city}.png                 # SME analysis
deg_{city}.png                 # Network degradation
fri_baseline_metrics.csv       # Baseline D&K metrics
fri_scenarios.csv              # All disruption scenarios
fri_failed_stations.csv        # Failed stations log
sme_results.csv                # SME by time threshold
```

## 10. Validation

### Singapore 2009 Validation
- Compare with historical D&K values
- Verify topology metrics match expected ranges
- Ensure FRI patterns align with network structure

### Cross-City Comparison
- NYC: Large, complex network
- Berlin: Medium, well-connected network
- Singapore: Compact, efficient network
- Singapore 2009: Historical baseline for growth analysis

## 11. References

1. Derrible, S., & Kennedy, C. (2009). Network Analysis of World Subway Systems Using Updated Graph Theory. Transportation Research Record, 2112(1), 17-25.

2. Derrible, S., & Kennedy, C. (2010). The complexity and robustness of metro networks. Physica A, 389(17), 3678-3691.

## 12. Code Repository Structure

```
code/
├── nyc_network_metrics.py           # NYC analysis
├── berlin_network_metrics.py        # Berlin analysis
├── singapore_network_metrics.py     # Singapore current
├── singapore_2009_validation.py     # Singapore 2009
├── METHODOLOGY_REPORT.md            # This document
├── input/                           # GTFS data
│   ├── nyc/
│   ├── berlin/
│   └── singapore/
└── outputs/                         # Results
    ├── nyc/
    ├── berlin/
    ├── singapore/
    └── singapore_2009/
```

## 13. Reproducibility

All scripts are self-contained and can be run independently:
```bash
python nyc_network_metrics.py
python berlin_network_metrics.py
python singapore_network_metrics.py
python singapore_2009_validation.py
```

Each script:
1. Loads GTFS data
2. Builds network topology
3. Calculates D&K metrics
4. Computes FRI and SME
5. Generates visualizations
6. Saves results to CSV

---

**Last Updated**: December 14, 2025
**Implementation**: Complete for all 4 cities with dual FRI analysis
