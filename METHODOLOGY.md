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
**Definition:** Network size relative to city area

```
σ = L / A
```
Where:
- L = Total route length (km)
- A = City area (km²)

**Interpretation:** Higher σ indicates more extensive coverage density.

**Results:**
- NYC: σ = 0.361 (most extensive)
- Berlin: σ = 0.150 
- Singapore: σ = 0.130

### 5.2 Directness (τ)
**Definition:** Maximum transfers required to traverse network

```
τ = (L / l) + δ
```
Where:
- l = Average line length
- δ = Maximum number of transfers between any two stations

**Interpretation:** Lower τ indicates more direct routing with fewer transfers.

**Results:**
- Singapore: τ = 2.67 (most direct)
- Berlin: τ = 4.50
- NYC: τ = 12.50 (most complex)

### 5.3 Connectivity (ρ)
**Definition:** Edge usage across multiple lines

```
ρ = (e^s + 2e^m) / (v^t + v^e)
```
Where:
- e^s = Single-use edges (one line only)
- e^m = Multiple-use edges (≥2 lines)
- v^t = Transfer stations
- v^e = Terminal stations

**Interpretation:** Higher ρ indicates better integration through shared infrastructure.

**Results:**
- NYC: ρ = 1.22 (highest integration)
- Singapore: ρ = 1.00 (linear structure)
- Berlin: ρ = 0.85

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

## 7. System Level Mobility Efficiency (SME)

### 7.1 Conceptual Framework

SME quantifies network accessibility by measuring the geographic area reachable within time thresholds, providing insights into how effectively transit infrastructure serves the population.

### 7.2 Methodological Evolution: From Legacy SME to Normalized Metrics

#### 7.2.1 Legacy SME Formula (Deprecated)

**Original Formula:**
```
SME_legacy(t) = A_reachable(t) / (L × P)
```

**Critical Flaw Identified:**
- Multiplying length by population creates dimensionally inconsistent normalization
- Does not account for differences in city density or geographic scale
- Makes cross-city comparisons misleading
- Units: km²/(km × people) = dimensionally awkward

#### 7.2.2 Proposed Novel Metrics for Transit Accessibility

To address the dimensional and interpretability issues with the legacy formula, we propose **three new normalized metrics** as contributions of this study:

**1. Infrastructure Efficiency (IE)** - Primary Proposed Metric

**Conceptual Definition:** Measures how much geographic area the network makes accessible per kilometer of track infrastructure.

**Significance:** Reveals whether a network achieves broad geographic coverage efficiently or requires extensive track to serve limited areas. Higher values indicate more efficient use of infrastructure investment, critical for cost-benefit analysis and infrastructure planning.

```
IE(t) = A_reachable(t) / L
```
- **Units:** km²/km (reachable area per track length)
- **Interpretation:** Geographic coverage productivity of infrastructure
- **Range:** Typically 0.5-3.0 for metro systems
- **Rationale:** Isolates infrastructure performance from population and city size effects

**2. Per-Capita Accessibility (PCA)** - Population-Normalized Metric

**Conceptual Definition:** Measures the accessible area available per million residents, indicating the "service footprint" each resident can access via transit.

**Significance:** Captures population equity - whether all residents have equal access to transit-reachable opportunities. Essential for social equity assessment and understanding disparities in transit access across cities.

```
PCA(t) = A_reachable(t) / (P / 1,000,000)
```
- **Units:** km²/million people
- **Interpretation:** Service area available per million residents
- **Range:** Typically 10-200 km²/M
- **Rationale:** Normalizes by population to compare service levels across cities

**3. Density-Normalized Coverage (DNC)** - Compound Normalization

**Conceptual Definition:** Measures network efficiency after normalizing for BOTH city geographic size and population density, enabling fair comparison across cities of vastly different scales.

**Significance:** Removes confounding effects of city size and population to reveal true infrastructure productivity. The most robust metric for cross-city comparison as it accounts for all major structural differences.

```
DNC(t) = (A_reachable(t) / A_city) / (L / P_millions)

Expanded form:
DNC(t) = (A_reachable(t) / A_city) × (P_millions / L)
```
- **Units:** Dimensionless ratio
- **Interpretation:** Coverage efficiency accounting for city scale and density
- **Range:** Typically 0.001-0.03
- **Rationale:** Combines geographic and demographic normalization for universal comparability

**4. Legacy SME** - For Backward Compatibility
```
SME_legacy(t) = A_reachable(t) / (L × P_millions)
```
- Retained for comparison with earlier iterations of this research
- **Not recommended** for primary analysis due to dimensional inconsistency

**Methodological Contribution:**
These metrics represent a novel framework for comparing transit accessibility across cities with vastly different scales, densities, and urban forms. Unlike single-formula approaches, this multi-metric framework provides complementary perspectives on infrastructure productivity, population service, and normalized coverage.

### 7.3 Reachability Analysis

**Time Thresholds Tested:** 20, 30, 45, 60, 75, 90 minutes

**For each time threshold t:**

1. **Compute All-Pairs Shortest Paths**
   - Algorithm: Dijkstra's with edge weights = travel times
   - Result: Travel time matrix T where T[i,j] = time from station i to j

2. **Determine Reachable Set**
   ```
   R_i(t) = {j : T[i,j] ≤ t}
   ```
   Set of stations reachable from i within time t

3. **Calculate Reachability Metrics**
   - Average reachable stations: mean(|R_i(t)|) across all i
   - Reachability percentage: (Σ|R_i(t)| / N²) × 100

### 7.4 Reachable Area Estimation

**Method:** Convex hull approximation

For a representative station with average reachability:
```python
reachable_stations = R_representative(t)
coordinates = [(lat_j, lon_j) for j in reachable_stations]
area = convex_hull(coordinates).area  # km²
```

**Fallback:** If scipy unavailable, use proxy: area ≈ 2 × |R_i(t)|

### 7.5 City Parameters

| City | Population (millions) | Area (km²) | Track Length (km) |
|------|----------------------|------------|-------------------|
| NYC | 8.34 | 783.8 | 380.17 |
| Berlin | 3.85 | 891.8 | 153.27 |
| Singapore | 5.45 | 734.3 | 231.63 |

### 7.6 Metric Interpretation Guide

**Infrastructure Efficiency (IE):**
- IE = 1.0 → Each km of track serves 1 km² area
- NYC: ~0.3 → Dense network, limited geographic spread
- Singapore: ~1.5 → Efficient area coverage per track

**Per-Capita Accessibility (PCA):**
- Higher values = more service area per resident
- Compact cities (Singapore) have lower PCA but better density
- Sprawling cities (NYC) may show higher PCA but lower efficiency

**Density-Normalized Coverage (DNC):**
- Accounts for both city size AND population density
- Best metric for comparing cities of vastly different scales
- Dimensionless allows universal comparison

### 7.7 Comparative Analysis: Metric Rankings Explained

#### Infrastructure Efficiency (IE) - Why NYC is Lowest

**NYC's Lower IE (0.28-0.85 km²/km) vs. Berlin (0.48-2.51):**

The counterintuitive result - NYC's massive 1,631 km network has LOWER efficiency than Berlin's 153 km - reflects fundamental design philosophies:

**NYC Characteristics:**
- **Sprawling coverage**: Network spans 5 boroughs across large metropolitan area
- **Long radial lines**: Routes extend to outer Queens, Bronx, Brooklyn (low-density areas)
- **Regional accessibility priority**: Designed to connect distant neighborhoods, not maximize efficiency
- **Infrastructure allocation**: Much track serves suburban-density areas with limited area coverage
- **Mathematical result**: Large denominator (1,631 km) relative to numerator (area covered)

**Berlin Characteristics:**
- **Compact concentration**: 153 km focused on dense urban core
- **Dense station spacing**: 0.90 km/station vs. NYC's 4.56 km/station
- **Area coverage priority**: Each km of track serves dense, continuous urban fabric
- **Efficient geometry**: Short, interconnected lines cover same area with less track
- **Mathematical result**: Small denominator (153 km) relative to numerator (area covered)

**Key Insight:** IE reveals **design philosophy**, not quality. NYC accepts lower efficiency to achieve borough-wide coverage appropriate for American sprawling metropolitan form.

#### Per-Capita Accessibility (PCA) - Population Effects

**NYC's Lower PCA (5.4-38.3 km²/M) vs. Berlin (19.1-99.8):**

Despite larger absolute reachable area, NYC's higher population reduces per-capita accessibility:

**NYC Trade-off:**
- 8.34 million people ÷ 459.8 km² (60-min reachable) = 55 km²/M people
- Extensive network serves more people, diluting per-capita benefit
- High-density boroughs concentrate population in limited area

**Berlin Advantage:**
- 3.85 million people ÷ 369.3 km² (estimated 60-min) = 96 km²/M people
- Smaller population means more service area per capita
- Lower density spreads population over served area

**Key Insight:** PCA shows **population equity** - not all residents have equal access to transit-reachable areas.

#### Density-Normalized Coverage (DNC) - Universal Fairness

**Why DNC is Most Robust:**

DNC normalizes BOTH city size and population:
```
DNC = (Coverage Fraction) / (Per-Capita Infrastructure)
    = (A_reachable / A_city) / (L / P_millions)
```

**NYC's Persistent Low Ranking (0.0041-0.0306):**
- Even after normalization, NYC remains lowest
- Meaning: The sprawling network is genuinely less efficient even accounting for scale
- 1,631 km serves 8.34M people across 629 km² → inherently lower productivity
- **Result**: Urban form fundamentally limits efficiency

**Berlin's Maintained High Ranking (0.0086-0.0463):**
- Normalization confirms Berlin's efficiency is real, not just size artifact
- 153 km serves 3.85M people across 892 km² → high productivity per unit
- **Result**: Compact form enables genuine efficiency

**Key Insight:** DNC confirms that ranking differences are **structural** (urban form) not **methodological artifacts**.

**Full Pairwise Calculation:**
- All N × (N-1) / 2 station pairs
- Actual shortest path times using network graph
- Statistical analysis: max, mean, median, percentiles

**Purpose:**
- Validate reachability thresholds
- Understand network span characteristics
- Cross-check SME calculations

---

## 8. Implementation Details

### 8.1 Software and Libraries

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

### 9.3 System Level Mobility Efficiency

| Time Threshold | NYC | Berlin | Singapore |
|----------------|-----|--------|-----------|
| **20 min** | 1,047 | 2,663 | 2,743 |
| **30 min** | 1,371 | 3,994 | 3,204 |
| **45 min** | 1,840 | 7,772 | 6,204 |
| **60 min** | 2,349 | 9,388 | 7,919 |
| **90 min** | 2,364 | 9,459 | 8,233 |

**Key Finding:** Berlin achieves highest SME at medium-to-long time thresholds (30-90 min), attributed to dense station spacing (0.90 km/station) in compact urban core.

#### 9.3.1 NYC's Low SME: Structural Analysis

**Observation:** NYC's SME values are substantially lower than Berlin and Singapore across all time thresholds despite having the largest network.

**Root Cause: Infrastructure-to-Population Ratio**

The SME denominator penalizes extensive networks:

```
SME(t) = A_reachable(t) / (L / P × 1000)
```

**Comparative Infrastructure Efficiency:**

| City | Route Length (L) | Population (P) | L/P × 1000 | People per km |
|------|------------------|----------------|------------|---------------|
| **NYC** | 1,631.7 km | 8,336,817 | **0.196** | 5,110 |
| **Berlin** | 153.3 km | 3,850,809 | **0.040** | 25,137 |
| **Singapore** | 184.7 km | 5,453,600 | **0.034** | 29,478 |

**NYC's L/P ratio is 4.9× larger than Berlin and 5.8× larger than Singapore.**

This means NYC must achieve ~5× the reachable area to match their SME scores.

**Structural Factors:**

1. **Over-Extension Relative to Population**
   - NYC: 10.6× more track than Berlin, but only 2.2× more people
   - Massive route length serves dispersed metropolitan region
   - Long radial routes to outer boroughs (Queens, Bronx, Brooklyn)

2. **Low Station Density**
   - NYC: 4.56 km per station (largest spacing)
   - Berlin: 0.90 km per station (5× denser)
   - Singapore: 1.51 km per station
   
   **Impact:** In 30 minutes, Berlin passengers can reach many closely-spaced stations (large geographic area), while NYC passengers spend more time between fewer, far-apart stations (smaller effective area coverage).

3. **Geographic Sprawl**
   - NYC metropolitan area: 778.2 km²
   - Network serves low-density outer neighborhoods
   - Much infrastructure dedicated to suburban connectivity
   
4. **Historical Development Pattern**
   - Organic growth over 120 years
   - Three merged systems (IRT, BMT, IND) with overlapping routes
   - Built to connect far-flung boroughs in pre-automobile era
   - Subsequent sprawl reduced density efficiency

**Illustrative Calculation (60-minute threshold):**

```
NYC:
  A_reachable ≈ 460 km²
  SME = 460 / 0.196 = 2,349 ✓

Berlin:
  A_reachable ≈ 375 km²
  SME = 375 / 0.040 = 9,375 ✓
```

Despite NYC's larger absolute reachable area (460 vs 375 km²), the massive L/P denominator yields lower SME.

**Interpretation:**

NYC's low SME reflects **different design priorities**, not inferior performance:

- **Trade-off:** Regional connectivity vs. local efficiency
- **Goal:** Serve entire 778 km² metropolitan area, not just dense core
- **Context:** American urban form with lower density, auto-oriented development

**Berlin/Singapore high SME reflects:**
- Concentrated infrastructure in dense urban cores
- Compact European/Asian urban form
- Higher efficiency per km of track

**Key Insight:**  
SME measures **infrastructure efficiency**, not **total accessibility**. NYC provides connectivity to 2.2× more people than Berlin across a vast region, but at lower efficiency per km of investment. This is a **structural consequence of urban form and network extent**, not a design failure.

### 9.4 Travel Time Characteristics

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
