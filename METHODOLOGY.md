# Urban Transit Network Analysis: Methodology Report
## Comparative Resilience and Efficiency Assessment of NYC, Berlin, and Singapore Metro Systems

---

## 1. Executive Summary

This study presents a comprehensive comparative analysis of three major urban transit networks—New York City Subway, Berlin U-Bahn, and Singapore MRT—using graph-theoretic approaches to quantify network topology, resilience, and accessibility. We employ Derrible & Kennedy complexity indicators, Functional Resilience Index (FRI), and System Level Mobility Efficiency (SME) metrics to evaluate how network structure influences operational performance and vulnerability to disruptions.

---

## 2. Study Objectives

### Primary Research Questions
1. How do topological network properties differ across cities with distinct development histories?
2. What is the comparative resilience of each network to random failures versus targeted attacks?
3. How does network structure affect accessibility and mobility efficiency?
4. What design principles emerge from comparing historical (NYC), reconstructed (Berlin), and planned (Singapore) systems?

---

## 3. Key Methodological Enhancement: Dual Delta (δ) Implementation

### 3.1 Delta Ambiguity in D&K Paper

**Problem Identified:** The Derrible & Kennedy (2009) paper uses "maximum number of transfers" to define delta (δ), but this terminology is ambiguous:
- **Interpretation 1 (δ_transfers):** Number of line changes required
- **Interpretation 2 (δ_trains):** Number of trains boarded (= line changes + 1)

### 3.2 Dual Implementation Solution

To resolve this ambiguity, we calculate **both** interpretations for all cities:

```python
delta_transfers = max_line_changes  # Maximum line changes needed
delta_trains = delta_transfers + 1   # Maximum trains boarded
tau_by_transfers = n_lines / delta_transfers
tau_by_trains = n_lines / delta_trains
```

### 3.3 Transfer Counting Algorithm

**BFS-Based Transfer Counter:**
```python
def count_min_transfers_bfs(G, source, target, topology):
    """
    Counts LINE changes, not station hops.
    Returns: (transfers, trains_boarded)
    """
    # Track which lines serve each edge
    # Count transfers when forced to switch lines
    # Return both interpretations
```

### 3.4 Dual FRI Analysis

Each city generates **two FRI resilience plots**:

**fri_transfers_{city}.png:**
- Uses τ = n_L / δ_transfers
- Shows resilience based on line changes interpretation

**fri_trains_{city}.png:**
- Uses τ = n_L / δ_trains  
- Shows resilience based on trains boarded interpretation

### 3.5 Performance Ratio Calculation

For each disruption scenario, we calculate dual performance ratios:

```python
# Baseline
baseline_bpc_transfers = predict_boardings_per_capita(σ, τ_transfers, ρ)
baseline_bpc_trains = predict_boardings_per_capita(σ, τ_trains, ρ)

# Disrupted scenario
bpc_by_transfers = predict_boardings_per_capita(σ_d, τ_d_transfers, ρ_d)
bpc_by_trains = predict_boardings_per_capita(σ_d, τ_d_trains, ρ_d)

performance_ratio_by_transfers = bpc_by_transfers / baseline_bpc_transfers
performance_ratio_by_trains = bpc_by_trains / baseline_bpc_trains
```

### 3.6 Validation Purpose

Comparing results from both interpretations against D&K reported values will determine which interpretation matches their methodology.

---

## 4. Data Sources and Processing

### 3.1 GTFS Data Acquisition

**Data Format:** General Transit Feed Specification (GTFS) static data

**Sources:**
- **NYC Subway:** Metropolitan Transportation Authority (MTA) GTFS feed
- **Berlin U-Bahn:** Berliner Verkehrsbetriebe (BVG) GTFS feed  
- **Singapore MRT:** Land Transport Authority (LTA) DataMall GTFS feed

**Key GTFS Components Used:**
- `routes.txt` - Transit line definitions
- `trips.txt` - Service patterns and schedules
- `stops.txt` - Station locations and identifiers
- `stop_times.txt` - Temporal sequences and dwell times
- `transfers.txt` - Inter-station transfer connections (where available)

### 3.2 Data Filtering and Preprocessing

**Network Scope:**
- **NYC:** 25 subway lines (excluding express variants and Staten Island Railway)
- **Berlin:** 9 U-Bahn lines (S-Bahn excluded as separate system)
- **Singapore:** 8 MRT heavy rail lines (LRT light rail excluded)

**Rationale:** Focus on heavy rail rapid transit to ensure methodological consistency across cities.

#### NYC-Specific Route Exclusions

The NYC MTA GTFS feed contains 29 route IDs classified as `route_type = 1` (subway). We exclude 4 routes:

**Excluded Routes:**

1. **6X (Pelham Express)** - EXCLUDED
   - Rationale: Express variant of line 6, not a separate service
   - Same physical route as 6 local, just skip-stop pattern
   - Including would double-count infrastructure

2. **7X (Flushing Express)** - EXCLUDED  
   - Rationale: Express variant of line 7
   - Peak-hour service overlay on 7 local route
   - Would create duplicate topology

3. **FX (Franklin Avenue Shuttle Express)** - EXCLUDED
   - Rationale: Express variant of Franklin Avenue Shuttle
   - Same route, different stopping pattern
   - Merged with base FS service

4. **SI (Staten Island Railway)** - EXCLUDED
   - Rationale: Operationally separate system
   - No physical connection to subway network
   - Different fare structure and rolling stock
   - More comparable to commuter rail than subway

**Impact:** Filtering reduces from 29 to **25 independent subway lines**.

**Validation:**  
The 25 lines match MTA's official subway map: numbered lines 1, 2, 3, 4, 5, 6, 7 and lettered lines A, B, C, D, E, F, G, J, L, M, N, Q, R, W, Z, plus shuttles (S, FS, H).

**Code Implementation:**
```python
# Filter for subway only (route_type == 1)
subway_routes_all = routes[routes['route_type'] == 1]

# Exclude express variants (ending with X) and Staten Island Railway
exclude_routes = subway_routes_all[
    (subway_routes_all['route_id'].str.endswith('X')) | 
    (subway_routes_all['route_id'] == 'SI')
]

subway_routes = subway_routes_all[
    ~subway_routes_all['route_id'].isin(exclude_routes['route_id'])
]
```

### 3.3 Station Identification and Grouping

**Challenge:** GTFS uses `stop_id` for individual platforms, but network analysis requires unique **stations** (multiple platforms grouped).

**Approach:**
```
1. Group stops by parent_station identifier where available
2. For stops without parent_station, use spatial proximity and name matching
3. Calculate station coordinates as centroid of constituent stops
4. Special handling for complex multi-system stations
```

**NYC-Specific Consideration:**  
NYC's GTFS reflects historical merger of three systems (IRT, BMT, IND). Some physically distinct stations share names (e.g., Gun Hill Rd appears twice at different locations). We use `parent_station` grouping to maintain topological accuracy while merging known multi-system transfer complexes based on documented physical connections.

**Final Station Counts:**
- NYC: 358 unique stations
- Berlin: 170 unique stations
- Singapore: 122 unique stations

---

## 4. Network Construction Methodology

### 4.1 Graph Representation

**Graph Type:** Undirected, weighted spatial network

**Nodes:** Transit stations (unique physical locations)

**Edges:** Direct connections between stations
- Source: Consecutive stops in GTFS trip sequences
- Weight: Travel time between stations (minutes)

**Travel Time Calculation:**
```python
travel_time = arrival_time(stop_i+1) - departure_time(stop_i)
# Averaged across all trips serving the segment
```

### 4.2 Dual Graph Structure

We construct **two graph representations** for each city:

#### 4.2.1 D&K Simplified Graph (FRI Analysis)
Following Derrible & Kennedy (2010):
- **Nodes:** Transfer stations (≥2 lines) and terminal stations only
- **Edges:** Direct connections between special vertices
- **Purpose:** Simplified topology for resilience analysis
- **Node Count:** 
  - NYC: 238 special vertices (221 transfer + 17 terminal)
  - Berlin: 41 special vertices (27 transfer + 14 terminal)
  - Singapore: 31 special vertices (23 transfer + 8 terminal)

#### 4.2.2 Full Graph (SME Analysis)
- **Nodes:** All 358/170/122 stations
- **Edges:** All direct station-to-station connections
- **Weights:** Actual travel times from GTFS
- **Purpose:** Accessibility and reachability analysis

---

## 5. Network Complexity Indicators (Derrible & Kennedy)

### 5.1 Coverage (σ)
**Definition:** Station coverage as fraction of city area

```
σ = (n_s × π × R²) / A
```
Where:
- n_s = Total number of stations
- R = Station catchment radius = 0.5 km (500 meters)
- A = City area (km²)
- π × R² = 0.785 km² (circular catchment area per station)

**Interpretation:** What fraction of the city is within walking distance (500m) of a station. Higher σ indicates better station coverage.

**Results:**
- NYC: σ = 0.447 (best coverage - 44.7% of city within 500m of a station)
- Berlin: σ = 0.150 
- Singapore: σ = 0.130

### 5.2 Directness (τ)
**Definition:** Ratio of lines to maximum required transfers

```
τ = n_L / δ
```
Where:
- n_L = Number of lines in the network
- δ = Maximum number of line transfers needed between any pair of transfer/terminal stations

**Interpretation:** Higher τ indicates more direct routing (fewer transfers relative to system size). Lower τ means complex routing requiring many transfers.

**Results:**
- Singapore: τ = 2.67 (8 lines / 3 max transfers - most direct)
- Berlin: τ = 4.50 (9 lines / 2 max transfers)
- NYC: τ = 12.50 (25 lines / 2 max transfers - most complex)

### 5.3 Connectivity (ρ)
**Definition:** Integration through transfer possibilities and shared infrastructure

```
ρ = (v_c^t - e^m) / v^t
```
Where:
- v_c^t = Sum of transfer possibilities = Σ(l_i - 1) for each transfer station with l_i lines
  - Station with 2 lines → 1 transfer possibility
  - Station with 3 lines → 2 transfer possibilities
  - Station with 4 lines → 3 transfer possibilities
- e^m = Number of multiple-use edges (track segments shared by ≥2 lines)
- v^t = Number of transfer stations

**Interpretation:** Higher ρ indicates better network integration through transfer hubs and shared infrastructure.

**Results:**
- NYC: ρ = 1.22 (highest integration - 221 transfer stations, 281 shared edges)
- Singapore: ρ = 1.00 (linear structure - 23 transfer stations, 2 shared edges)
- Berlin: ρ = 0.85 (moderate integration - 27 transfer stations, 14 shared edges)

### 5.4 Predicted Boardings per Capita
D&K regression model for ridership prediction:

```
Bpc = 44.963σ + 7.579τ + 92.316ρ + 102.947
```

**Results:**
- NYC: 326.7 boardings/capita/year
- Berlin: 222.4 boardings/capita/year
- Singapore: 221.3 boardings/capita/year

---

## 6. Functional Resilience Index (FRI)

### 6.1 Conceptual Framework

FRI measures network performance degradation under station failures, assessing both random disruptions and targeted attacks.

**Performance Metric:**  
Boardings per capita (Bpc) combines network topology and city characteristics

**Performance Ratio with Fragmentation Penalty:**
```
PR = (Bpc_disrupted / Bpc_baseline) × FragmentationPenalty
```

Where:
- Bpc_disrupted = Predicted boardings per capita after station failures
- Bpc_baseline = Baseline boardings per capita (intact network)
- FragmentationPenalty accounts for network splitting

### 6.1.1 Network Reduction and Fragmentation Impact

**Conceptual Framework:**

When stations fail, network performance degrades through two distinct mechanisms:

1. **Network Size Reduction:** Fewer stations available (even if still connected)
2. **Network Fragmentation:** Splitting into disconnected components

The D&K indicators (σ, τ, ρ) only describe the **largest connected component** topology, failing to capture either of these degradation modes comprehensively.

#### Network Size Penalty (Incorrectly Called "Fragmentation Penalty")

**IMPORTANT CLARIFICATION:** The term "fragmentation penalty" in our implementation is a **misnomer**. It actually applies uniformly to all station removals, regardless of whether fragmentation occurs.

**Mathematical Formulation:**

```
SizePenalty = N_remaining / N_baseline
```

Where:
- N_remaining = Number of nodes in disrupted graph (all components)
- N_baseline = Number of nodes in baseline graph

**Full Performance Ratio:**
```
PR = (Bpc_disrupted / Bpc_baseline) × (N_remaining / N_baseline)
           ↑                                    ↑
    Topological degradation            Network size penalty
```

**Critical Point:** This penalty applies **unconditionally**, even when the network remains fully connected!

#### Example Scenarios Corrected

**Example 1: No Fragmentation (Size Reduction Only)**

Initial network: 100 stations, fully connected  
Disruption: Remove 10 peripheral stations  
Result: 90 stations, **still fully connected** (1 component)

```
N_baseline = 100
N_remaining = 90
SizePenalty = 90/100 = 0.90

Bpc_baseline = 250
Bpc_disrupted = 245 (slightly lower due to reduced σ, τ, ρ)

PR = (245/250) × 0.90 = 0.98 × 0.90 = 0.882
       ↑                   ↑
   Topological      Size penalty
   (minor impact)   (10% fewer stations)
```

**Interpretation:** Even though the network stayed connected, there's a 10% penalty simply for having fewer stations. The user is correct—this isn't truly a "fragmentation" penalty!

**Example 2: Severe Fragmentation**

Initial network: 100 stations, fully connected  
Disruption: Remove 10 critical transfer hubs  
Result: Network splits into 5 disconnected components

```
Components: [50, 20, 10, 5, 5] stations

N_baseline = 100
N_remaining = 90 (sum of all component sizes)
SizePenalty = 90/100 = 0.90

Bpc_baseline = 250
Bpc_disrupted = 180 (D&K indicators computed on largest component only!)

PR = (180/250) × 0.90 = 0.72 × 0.90 = 0.648
       ↑                   ↑
   Topological      Size penalty
   (significant)    (same 10% as Example 1!)
```

**Critical Observation:**  
- Same size penalty (0.90) as Example 1
- But **much worse** topological degradation (0.72 vs 0.98)
- Total PR: 0.648 vs 0.882 (fragmentation matters!)

**However, the size penalty itself doesn't distinguish between these scenarios!**

#### True Fragmentation Impact: Reachable Pairs Metric

To properly capture fragmentation severity, we compute **reachable pairs percentage**:

**Definition:**
```
For each component Cᵢ:
    reachable_pairsᵢ = |Cᵢ| × (|Cᵢ| - 1) / 2

total_reachable = Σ reachable_pairsᵢ
total_possible = N_baseline × (N_baseline - 1) / 2

reachable_pct = (total_reachable / total_possible) × 100
```

**Example 1 Revisited (Connected):**

```
Component: [90 stations]

Reachable pairs: 90 × 89 / 2 = 4,005
Total possible (baseline): 100 × 99 / 2 = 4,950

Reachability: 4,005 / 4,950 = 80.9%
```

Despite removing only 10 stations (10% size reduction), reachability drops to 81% due to quadratic nature of pair counting.

**Example 2 Revisited (Fragmented):**

```
Components: [50, 20, 10, 5, 5]

Reachable pairs per component:
C₁: 50 × 49 / 2 = 1,225
C₂: 20 × 19 / 2 = 190
C₃: 10 × 9 / 2 = 45
C₄: 5 × 4 / 2 = 10
C₅: 5 × 4 / 2 = 10

Total reachable: 1,480 pairs
Total possible: 4,950 pairs

Reachability: 1,480 / 4,950 = 29.9%
```

**Now the difference is clear!**
- Example 1 (connected): 80.9% reachability
- Example 2 (fragmented): 29.9% reachability

#### Comparison of Metrics

| Metric | Example 1 (Connected) | Example 2 (Fragmented) | Distinguishes? |
|--------|----------------------|------------------------|----------------|
| **Size Penalty** | 0.90 | 0.90 | ❌ No |
| **Reachable Pairs %** | 80.9% | 29.9% | ✅ Yes |
| **Isolated Stations** | 0 | 40 | ✅ Yes |

**Correct Interpretation:**

```
PR_topology = Bpc_disrupted / Bpc_baseline  # D&K topological performance
PR_size = N_remaining / N_baseline          # Network size reduction (NOT fragmentation!)
PR_connectivity = reachable_pct / 100       # TRUE fragmentation impact

Final_PR = PR_topology × PR_size  # What we actually compute
```

We report **three independent metrics**:
1. **Performance Ratio (PR):** Combines topology + size
2. **Isolated Stations:** Count of stations cut off
3. **Reachable Pairs %:** True connectivity preservation measure

#### Enhanced Degradation Metric: Reachable Pairs

To capture fragmentation severity beyond simple node count, we compute **reachable pairs percentage**:

```
For each component Cᵢ:
    reachable_pairsᵢ = |Cᵢ| × (|Cᵢ| - 1) / 2

total_reachable = Σ reachable_pairsᵢ
total_possible = N × (N - 1) / 2

reachable_pct = (total_reachable / total_possible) × 100
```

**Example 2 Revised:**

```
Component sizes: [50, 20, 10, 5, 5]

Reachable pairs per component:
C₁: 50 × 49 / 2 = 1,225
C₂: 20 × 19 / 2 = 190
C₃: 10 × 9 / 2 = 45
C₄: 5 × 4 / 2 = 10
C₅: 5 × 4 / 2 = 10

Total reachable: 1,480 pairs
Total possible (intact): 100 × 99 / 2 = 4,950 pairs

Reachability: 1,480 / 4,950 = 29.9%
```

**Interpretation:** Only 29.9% of station pairs remain reachable, far more severe than the 90% suggested by simple node count penalty!

#### Fragmentation Penalty vs. Reachability

| Metric | Captures | Limitation |
|--------|----------|------------|
| **Fragmentation Penalty** | Network size reduction | Treats all components equally |
| **Reachable Pairs %** | Actual connectivity loss | More nuanced fragmentation severity |

**Combined Usage:**

```
PR_topology = Bpc_disrupted / Bpc_baseline  # Topological performance
PR_fragmentation = N_remaining / N_baseline  # Size penalty
PR_connectivity = reachable_pct / 100       # Connectivity preservation

Final PR = PR_topology × PR_fragmentation
```

We report both FragmentationPenalty (for FRI) and Reachable Pairs % (for detailed degradation analysis).

#### Real-World Implications

**Low Fragmentation (High Redundancy):**
- Multiple alternative routes exist
- Failure of one station has localized impact
- Network maintains overall connectivity
- Example: NYC with parallel lines in Manhattan

**High Fragmentation (Critical Nodes):**
- Single points of failure exist
- Removal of key transfer hubs isolates entire branches
- Cascading service disruption
- Example: Linear systems with few transfer points

**Design Insight:**  
Networks with higher connectivity (ρ) and more transfer stations tend to exhibit lower fragmentation under random failures, but may be more vulnerable to targeted attacks on high-degree nodes.

### 6.2 Disruption Scenarios

#### 6.2.1 Random Failures
Simulates equipment breakdowns, accidents, or unpredictable events.

**Probabilities Tested:** 5%, 10%, 15%, 20% of stations
**Trials per Probability:** 10 independent random selections
**Total Random Scenarios:** 40 per city

**Procedure:**
```
For each probability p:
    For trial = 1 to 10:
        1. Randomly select p × N stations
        2. Remove from network
        3. Recalculate topology indicators
        4. Compute performance ratio
    Average performance across 10 trials → FRI(p)
```

#### 6.2.2 Targeted Attacks: Degree-Based
Simulates strategic disruption of highest-traffic hubs.

**Attack Method:** Remove k stations with highest degree (most connections)
**k values:** 1, 2, 3, 4, 5, 6, 7, 8 stations
**Total Scenarios:** 8 per city

**Rationale:** High-degree stations often correspond to major transfer hubs with high passenger volume.

#### 6.2.3 Targeted Attacks: Betweenness-Based
Simulates disruption of most critical routing points.

**Attack Method:** Remove k stations with highest betweenness centrality
**k values:** 1, 2, 3, 4, 5, 6, 7, 8 stations
**Total Scenarios:** 8 per city

**Betweenness Centrality:**
```
BC(v) = Σ(σ_st(v) / σ_st)
```
Where σ_st(v) = number of shortest paths through vertex v

**Rationale:** High betweenness indicates nodes critical for network-wide connectivity.

### 6.3 FRI Calculation

**Overall FRI** = Average performance ratio across all disruption scenarios

**Scenario-Specific FRI:**
- FRI_random = Average across random failure scenarios
- FRI_degree = Average across degree-based attacks
- FRI_betweenness = Average across betweenness-based attacks

### 6.4 Network Degradation Metrics

#### 6.4.1 Isolated Stations
Count of stations disconnected from largest connected component.

**Calculation:**
```python
components = connected_components(G_disrupted)
largest = max(components, key=len)
isolated = N_total - len(largest)
```

#### 6.4.2 Reachable Pairs Percentage
Fraction of station pairs that maintain connectivity.

**Calculation:**
```
reachable_pairs = Σ(n_c × (n_c - 1) / 2) for all components c
total_pairs = N × (N - 1) / 2
reachable_pct = (reachable_pairs / total_pairs) × 100
```

---

## 7. Transit Accessibility Metrics

### 7.1 Conceptual Overview

Transit accessibility measures **how well transit networks connect people to geographic opportunities** within time constraints. Unlike topological metrics (which measure network structure), accessibility metrics evaluate **functional performance** - what areas riders can actually reach.

**Core Concept:** A transit network's value depends not just on how it's built (connectivity, density) but on **what it enables riders to access** (jobs, services, amenities) within reasonable travel times.

**Why Three Metrics?** Different stakeholders care about different aspects:
- **Infrastructure planners** → IE (return on infrastructure investment)
- **Equity advocates** → PCA (fairness of access across population)
- **Comparative researchers** → DNC (fair cross-city comparison)

### 7.2 Metric Definitions and Rationale

#### 7.2.1 Infrastructure Efficiency (IE)

**Definition:**
```
IE(t) = A_reachable(t) / L
```

**What it measures:** Geographic area (km²) accessible within time t per kilometer of track infrastructure.

**Units:** km²/km (area per length)

**Interpretation Guide:**
- IE = 1.0 → Each km of track provides access to 1 km² of area
- IE = 2.5 → Each km of track provides access to 2.5 km² (high efficiency)
- IE = 0.3 → Each km of track provides access to only 0.3 km² (low efficiency)

**Why this metric matters:**
- **Infrastructure ROI**: Shows geographic coverage return per km of expensive track
- **Planning tool**: Identifies whether expansions should focus on new coverage vs. density
- **Design diagnosis**: Low IE may indicate over-extension or sprawling network design

**Real-world application:** If Berlin achieves IE = 2.5 km²/km while NYC achieves 0.3 km²/km, Berlin gets **8× more area coverage per infrastructure dollar invested**.

**Writing tip:** When describing IE results, always explain WHY one city has higher efficiency (compact form, dense station spacing, targeted corridors) rather than just presenting numbers.

#### 7.2.2 Per-Capita Accessibility (PCA)

**Definition:**
```
PCA(t) = A_reachable(t) / (P / 1,000,000)
```

**What it measures:** Geographic area (km²) accessible via transit per million residents.

**Units:** km²/M (area per million people)

**Interpretation Guide:**
- PCA = 50 km²/M → Each million residents can access 50 km² of the city
- PCA = 100 km²/M → Double the per-capita access (either more area OR fewer people)
- Higher PCA → More equitable access OR lower population density

**Why this metric matters:**
- **Social equity**: Reveals whether all residents have equal access to opportunities
- **Service fairness**: High population shouldn't mean low per-capita access
- **Quality of life**: More accessible area means more job/service choices per person

**Critical distinction:** PCA is **NOT** proportional to network size. NYC has the largest network but lowest PCA because its huge population (8.34M) dilutes per-capita benefits.

**Writing tip:** When discussing PCA, always contextualize with population size. "Berlin's higher PCA (96 km²/M) reflects its smaller population (3.85M) enjoying moderate area coverage, versus NYC's larger population (8.34M) sharing extensive but diluted access."

#### 7.2.3 Density-Normalized Coverage (DNC)

**Definition:**
```
DNC(t) = (A_reachable(t) / A_city) / (L / P_millions)

Expanded form:
DNC(t) = (A_reachable(t) / A_city) × (P_millions / L)
```

**What it measures:** Network efficiency after removing confounding effects of city size and population density.

**Units:** Dimensionless ratio (no units)

**Interpretation Guide:**
- DNC is a **relative efficiency score**
- Higher DNC → Better infrastructure productivity relative to city scale
- Enables fair comparison between NYC (784 km², 8.3M) and Berlin (892 km², 3.9M)

**Why this normalization is crucial:**

DNC combines two normalization steps:
1. **Geographic normalization**: (A_reachable / A_city)
   - What fraction of the city's total area is accessible?
   - Controls for city size differences

2. **Infrastructure density normalization**: (L / P_millions)
   - How much track exists per million residents?
   - Controls for population size and infrastructure investment

**Key insight:** DNC reveals whether efficiency differences are due to:
- **Urban form** (compact vs. sprawling) → affects A_reachable/A_city
- **Infrastructure strategy** (dense vs. sparse) → affects L/P_millions
- OR both

**Writing tip:** When presenting DNC results, explain that it "levels the playing field" by accounting for all confounding factors. Berlin's higher DNC (0.0445) vs. NYC (0.0221) means Berlin is **genuinely more efficient** even after controlling for size and population.

### 7.3 Computation Methodology

**Step-by-Step Process:**

1. **Calculate All-Pairs Shortest Paths**
   ```
   For each station pair (i, j):
       T[i,j] = shortest travel time from i to j using network graph
   ```
   - Algorithm: Dijkstra's shortest path
   - Edge weights: scheduled travel times from GTFS
   - Result: N × N travel time matrix

2. **Identify Reachable Stations**
   ```
   For each time threshold t (20, 30, 45, 60, 75, 90 minutes):
       For each station i:
           R_i(t) = {j : T[i,j] ≤ t}  # Set of reachable stations
   ```

3. **Estimate Reachable Area**
   ```python
   # For a representative station with median reachability
   representative_station = find_station_with_median_reachability(t)
   reachable_set = R_representative(t)
   
   # Get coordinates of all reachable stations
   coordinates = [(lat_j, lon_j) for j in reachable_set]
   
   # Compute convex hull area
   hull = ConvexHull(coordinates)
   A_reachable(t) = hull.area  # in km²
   ```

4. **Calculate Metrics**
   ```python
   IE(t) = A_reachable(t) / L
   PCA(t) = A_reachable(t) / (P / 1_000_000)
   DNC(t) = (A_reachable(t) / A_city) / (L / P_millions)
   ```

**Time Thresholds Explained:**
- **20-30 min**: Typical commute tolerance, local accessibility
- **45-60 min**: Medium-distance trips, city-wide access
- **75-90 min**: Long trips, full network reach

### 7.4 Results Interpretation Framework

**How to write about IE results:**

Template: "Berlin achieves IE of [value] km²/km at the [time] threshold, indicating that each kilometer of track infrastructure provides access to [value] square kilometers of urban area. This is [X]× higher than NYC ([value] km²/km), primarily due to [explain urban form difference: compact vs. sprawling, station density, network design]."

Example: "Berlin achieves IE of 2.41 km²/km at the 60-minute threshold, indicating that each kilometer of track infrastructure provides access to 2.41 square kilometers of urban area. This is 8.6× higher than NYC (0.28 km²/km), primarily due to Berlin's compact urban core (153 km network serving 892 km² city) versus NYC's sprawling metropolitan coverage (1,631 km network across 784 km² with low-density outer boroughs)."

**How to write about PCA results:**

Template: "Berlin residents enjoy PCA of [value] km²/M at [time] minutes, meaning each million residents can access [value] square kilometers of the city via transit. This [comparison to other cities], reflecting [explain population and urban form factors]."

Example: "Berlin residents enjoy PCA of 95.8 km²/M at 60 minutes, meaning each million residents can access nearly 96 square kilometers of the city via transit. This is 3.5× higher than NYC (27.5 km²/M), reflecting Berlin's smaller population (3.85M vs. 8.34M) and moderate network coverage creating higher per-capita accessibility despite NYC's larger absolute reachable area."

**How to write about DNC results:**

Template: "After normalizing for both city size and population density, [city] achieves DNC of [value], [comparison], indicating that [interpretation of genuine efficiency difference based on urban form]."

Example: "After normalizing for both city size and population density, Berlin achieves DNC of 0.0445, 2× higher than NYC (0.0221), indicating that Berlin's compact European urban form genuinely enables more efficient infrastructure productivity than NYC's sprawling American metropolitan pattern."

### 7.5 Cross-City Comparison Guidelines

**When writing comparative analysis:**

1. **Always explain the "why" behind differences:**
   - ✅ "Berlin's higher IE stems from its compact 153 km U-Bahn serving a dense 892 km² core"
   - ❌ "Berlin has higher IE than NYC" (too vague)

2. **Contextualize with urban form:**
   - Mention city area, population, network length
   - Explain historical development (organic vs planned)
   - Note density differences

3. **Avoid value judgments:**
   - ✅ "NYC's lower IE reflects its design priority for regional connectivity over infrastructure efficiency"
   - ❌ "NYC's network is inefficient" (misleading - it serves different goals)

4. **Use all three metrics together:**
   - IE shows infrastructure productivity
   - PCA shows population equity
   - DNC confirms if differences are real or size artifacts

### 7.6 Key Findings Summary (Example Writing)

**This section provides example text that can be adapted:**

"Analysis of transit accessibility across NYC, Berlin, and Singapore reveals distinct efficiency profiles shaped by urban form and design priorities:

**Infrastructure Efficiency** demonstrates Berlin's leadership (IE: 0.48-2.51 km²/km) compared to Singapore (0.39-1.84 km²/km) and NYC (0.13-0.28 km²/km). Berlin's compact 153 km network concentrated in a dense urban core achieves 2-3× more area coverage per kilometer of track than other cities. NYC's lower IE reflects its sprawling 1,631 km network serving a dispersed metropolitan region including low-density outer boroughs.

**Per-Capita Accessibility** similarly favors Berlin (19-100 km²/M) over Singapore (13-62 km²/M) and NYC (5-38 km²/M). Berlin's smaller population (3.85M)享 enjoys disproportionate benefits from moderate network coverage, while NYC's large population (8.34M) dilutes per-capita accessibility despite its extensive infrastructure.

**Density-Normalized Coverage** confirms these efficiency differences are structural rather than artifactual. After controlling for city size and population density, Berlin maintains its lead (DNC: 0.0086-0.0463), with Singapore close behind (0.0085-0.0402) and NYC trailing (0.0041-0.0306). This indicates that urban form - not just network size - fundamentally determines infrastructure productivity."

---

## 8. Implementation Details

### 7.1 Software and Libraries

**Language:** Python 3.8+

**Core Dependencies:**
- `pandas` (1.5+) - GTFS data processing
- `numpy` (1.23+) - Numerical computations
- `networkx` (2.8+) - Graph algorithms and analysis
- `matplotlib` (3.5+) - Visualization
- `scipy` (1.9+) - Spatial computations (convex hull)
- `haversine` - Geographic distance calculations

### 8.2 Computational Approach

**Graph Construction:**
```python
G = nx.Graph()
G.add_nodes_from(stations)
G.add_weighted_edges_from(
    (s1, s2, travel_time) for consecutive stops in trips
)
```

**Shortest Path Algorithm:** Dijkstra's algorithm with travel time weights

**FRI Scenarios:** Sequential computation with progress tracking

**Parallelization:** Single-threaded (NetworkX graph operations not thread-safe)

### 8.3 Data Validation

**Connectivity Verification:**
- All final graphs confirmed as single connected component
- Station count validation against published MTA/BVG/LTA statistics
- Geographic sanity checks (coordinates within city bounds)

**Temporal Consistency:**
- Travel times positive and non-zero
- Average speeds within reasonable subway range (20-40 km/h)
- No temporal paradoxes in stop_times sequences

---

## 9. Key Results Summary

### 9.1 Network Topology

| Metric | NYC | Berlin | Singapore |
|--------|-----|--------|-----------|
| **Stations** | 358 | 170 | 122 |
| **Route Length (km)** | 1,631.7 | 153.3 | 184.7 |
| **Coverage (σ)** | 0.361 | 0.150 | 0.130 |
| **Directness (τ)** | 12.50 | 4.50 | 2.67 |
| **Connectivity (ρ)** | 1.22 | 0.85 | 1.00 |

### 9.2 Functional Resilience Index

| City | Overall FRI | Random | Degree | Betweenness |
|------|-------------|--------|--------|-------------|
| **Singapore** | 0.8724 | 0.8849 | 0.8324 | 0.8498 |
| **Berlin** | 0.7976 | 0.8031 | 0.7835 | 0.7845 |
| **NYC** | 0.7285 | 0.7029 | 0.8104 | 0.7745 |

**Key Finding:** Singapore demonstrates highest resilience across all attack types, while NYC shows particular vulnerability to random failures but better resistance to degree-based attacks.

---

## 10. Limitations and Assumptions

### 9.3 Travel Time Characteristics

| City | Max Time | Mean Time | Median Time |
|------|----------|-----------|-------------|
| **NYC** | 80.3 min | 21.8 min | 20.1 min |
| **Berlin** | 73.0 min | 21.6 min | 20.0 min |
| **Singapore** | 93.0 min | 25.6 min | 23.0 min |

---

## 10. Methodological Considerations

### 10.1 Assumptions and Limitations

**GTFS Data Accuracy:**
- Represents scheduled service, not real-time operations
- Does not account for service variations, delays, or disruptions
- Transfer times estimated uniformly (may vary by station)

**Network Simplifications:**
- Bidirectional edges (same travel time both directions)
- Static network (no temporal variations in service patterns)
- Ignores capacity constraints and crowding effects

**Geographic Scope:**
- Analysis limited to heavy rail systems
- Excludes bus, tram, and light rail connections
- City boundaries may not reflect full metropolitan area

### 10.2 Reproducibility

**Data Versioning:**
- GTFS feeds timestamped at download
- Specific route/station counts documented
- Exclusion criteria explicitly defined

**Random Seed Control:**
```python
np.random.seed(42)  # For reproducible random failure scenarios
```

**Code Availability:**
All analysis scripts, data processing pipelines, and visualization code documented in project repository.

---

## 11. Comparative Analysis Insights

### 11.1 Historical vs. Planned Systems

**NYC (Historical Merger):**
- Organic growth through merger of three independent systems
- High connectivity (ρ=1.22) from redundant routes
- Complex transfer structure (τ=12.5) reflects multi-system legacy
- Vulnerable to random failures due to aged infrastructure

**Berlin (Post-Reunification Reconstruction):**
- Integrated East/West networks after 1989
- Balanced resilience across attack types
- Optimized for dense urban core coverage
- Highest SME at medium ranges (45-60 min)

**Singapore (Modern Planned Network):**
- Purpose-built integrated system
- Most direct routing (τ=2.67)
- Highest overall resilience (FRI=0.87)
- Linear corridor design with strategic interchange points

### 11.2 Design Trade-offs

**Coverage vs. Density:**
- NYC: Maximum coverage (σ=0.36) but stations spread thin (4.56 km/station)
- Berlin: Moderate coverage (σ=0.15) with dense stations (0.90 km/station)
- Singapore: Compact coverage (σ=0.13) with strategic placement

**Redundancy vs. Simplicity:**
- NYC: High redundancy (multiple routes between key stations) → complexity
- Singapore: Minimal redundancy (linear corridors) → simplicity and directness
- Berlin: Moderate approach balancing both

---

## 12. Conclusions

This methodology enables quantitative comparison of transit network structure, resilience, and accessibility across cities with fundamentally different development contexts. The tri-metric approach (D&K indicators, FRI, SME) provides complementary perspectives:

1. **D&K Indicators** characterize inherent topological properties
2. **FRI** quantifies robustness to disruptions
3. **SME** measures practical accessibility for users

Results demonstrate that network resilience and efficiency are not solely functions of size or density, but emerge from the interplay of topological structure, geographic constraints, and design philosophy. Modern planned systems (Singapore) can achieve superior resilience through strategic design, while historic systems (NYC, Berlin) must balance legacy constraints with incremental improvements.

---

## References

Derrible, S., & Kennedy, C. (2010). The complexity and robustness of metro networks. *Physica A: Statistical Mechanics and its Applications*, 389(17), 3678-3691.

Derrible, S., & Kennedy, C. (2011). Applications of graph theory and network science to transit network design. *Transport Reviews*, 31(4), 495-519.

---

*Report Generated: December 2024*  
*Analysis Period: 2024 GTFS Data*  
*Methodology: Derrible & Kennedy (2010) Framework*
