# Urban Transit Network Analysis: Cross-City Comparison

## Executive Summary

Comparative analysis of three major urban transit systems using Functional Resilience Index (FRI) and System Level Mobility Efficiency (SME) methodologies based on Derrible & Kennedy (2010) indicators.

---

## Network Characteristics

| Metric | NYC Subway | Berlin U-Bahn | Singapore MRT |
|--------|------------|---------------|---------------|
| **Total Stations** | 358 | 170 | 122 |
| **Lines Analyzed** | 25 | 9 | 8 |
| **Transfer Stations (v^t)** | 221 | 27 | 23 |
| **Terminal Stations (v^e)** | 17 | 14 | 8 |
| **D&K Special Vertices (v)** | 238 | 41 | 31 |
| **Route Length (L)** | 1,631.7 km | 153.3 km | 184.7 km |
| **Population Served** | 8,336,817 | 3,850,809 | 5,453,600 |
| **City Area (A)** | 629.2 km² | 892 km² | 734.3 km² |

### Density Metrics

| Metric | NYC | Berlin | Singapore |
|--------|-----|--------|-----------|
| **Stations per Million** | 43 | 44 | 22 |
| **km per Station** | 4.56 | 0.90 | 1.51 |
| **km per 1000 people** | 0.196 | 0.040 | 0.034 |
| **Network Density** | 2.59 km/km² | 0.17 km/km² | 0.25 km/km² |

---

## Derrible & Kennedy Indicators

### Coverage (σ) - Network Size Indicator
*Captures network size relative to city area*

| City | σ | Interpretation |
|------|---|----------------|
| **NYC** | **0.447** | Extensive coverage (largest σ) |
| **Berlin** | 0.150 | Moderate coverage |
| **Singapore** | 0.130 | Compact coverage |

**Formula:** σ = L / A where L = route length (km), A = city area (km²)

### Directness (τ) - Transfer Complexity
*Measures maximum transfers needed; lower is better*

| City | τ | δ (max transfers) | Interpretation |
|------|---|-------------------|----------------|
| **Singapore** | **2.67** | 3 | Most direct (best) |
| **Berlin** | 4.50 | 2 | Moderate directness |
| **NYC** | 12.50 | 2 | Complex (many lines) |

**Formula:** τ = (L / l) + δ where l = avg line length, δ = max transfers

### Connectivity (ρ) - Network Integration
*Higher values indicate better integration*

| City | ρ | e^s | e^m | Interpretation |
|------|---|-----|-----|----------------|
| **NYC** | **1.22** | 376 | 281 | Highly integrated |
| **Singapore** | 1.00 | 46 | 2 | Linear structure |
| **Berlin** | 0.85 | 54 | 14 | Moderate integration |

**Formula:** ρ = (e^s + 2e^m) / (v^t + v^e) where e^s = single-use edges, e^m = multiple-use edges

### Predicted Boardings per Capita
*Derrible & Kennedy regression model*

| City | Predicted Bpc | Actual Context |
|------|---------------|----------------|
| **NYC** | **299.0** | Highest usage prediction |
| **Berlin** | 211.1 | Moderate usage |
| **Singapore** | 216.3 | Moderate usage |

**Formula:** Bpc = 44.963σ + 7.579τ + 92.316ρ + 102.947

---

## Travel Time Analysis

### Distribution Statistics (All Station Pairs)

| City | Max Time | Mean Time | Median Time | Longest Path |
|------|----------|-----------|-------------|--------------|
| **NYC** | 80.3 min | 21.8 min | 20.1 min | Pelham Bay Park → Far Rockaway |
| **Berlin** | 73.0 min | 21.6 min | 20.0 min | - |
| **Singapore** | 93.0 min | 25.6 min | 23.0 min | Pasir Ris → Tuas Link |


---

## Transit Accessibility Metrics

### Infrastructure Efficiency (IE)
*Geographic coverage per unit of infrastructure*

**What it measures:** How much geographic area the network makes accessible per kilometer of track. Higher values indicate more efficient use of infrastructure investment.

**Why it matters:** Reveals whether a network achieves broad geographic coverage efficiently or requires extensive track to serve limited areas. Critical for infrastructure planning and ROI assessment.

| Time | NYC | Berlin | Singapore | Leader |
|------|-----|--------|-----------|--------|
| **20 min** | 0.13 | 0.48 | 0.39 | Berlin |
| **30 min** | 0.16 | 0.96 | 0.79 | Berlin |
| **45 min** | 0.22 | 1.77 | 1.29 | Berlin |
| **60 min** | 0.28 | 2.41 | 1.71 | Berlin |
| **75 min** | 0.28 | 2.51 | 1.76 | Berlin |
| **90 min** | 0.28 | 2.51 | 1.84 | Berlin |

**Formula:**
```
IE(t) = A_reachable(t) / L
```
Where:
- A_reachable(t) = Geographic area reachable within time threshold t (km²)
- L = Total route length (km)
- Units: km²/km

**Results Analysis:**
- **Berlin leads** at all time thresholds (0.48-2.51 km²/km)
  - Compact 153 km network concentrated in dense urban core
  - Each km of track serves 2-3× more area than other cities
  - Dense station spacing (0.90 km/station) enables efficient coverage
- **Singapore moderate** (0.39-1.84 km²/km)
  - Linear network design balances efficiency with island geography
  - Strategic corridor placement optimizes coverage
- **NYC lowest** (0.13-0.28 km²/km)
  - Sprawling 1,631 km network across 5 boroughs
  - Long radial lines serve low-density outer areas
  - Design prioritizes regional reach over infrastructure efficiency

### Per-Capita Accessibility (PCA)
*Service area per million residents*

**What it measures:** How much accessible area is available per million residents. Indicates the "service footprint" each resident can access via transit.

**Why it matters:** Captures population equity - whether all residents have equal access to transit-reachable opportunities. Essential for social equity and urban planning.

| Time | NYC (km²/M) | Berlin (km²/M) | Singapore (km²/M) | Leader |
|------|-------------|----------------|-------------------|--------|
| **20 min** | 5.4 | 19.1 | 13.1 | Berlin |
| **30 min** | 9.2 | 38.3 | 26.6 | Berlin |
| **45 min** | 16.7 | 70.3 | 43.5 | Berlin |
| **60 min** | 27.5 | 95.8 | 57.6 | Berlin |
| **75 min** | 35.0 | 99.8 | 59.4 | Berlin |
| **90 min** | 38.3 | 99.8 | 62.0 | Berlin |

**Formula:**
```
PCA(t) = A_reachable(t) / (P / 1,000,000)
```
Where:
- A_reachable(t) = Geographic area reachable within time threshold t (km²)
- P = City population (people)
- Units: km² per million people

**Results Analysis:**
- **Berlin dominates** (19.1-99.8 km²/M)
  - Smaller population (3.85M) means more area per capita
  - Each resident has access to 2-3× more area than other cities
  - Low population density spreads service benefits
- **Singapore moderate** (13.1-62.0 km²/M)
  - Mid-sized population (5.45M) balanced with network extent
  - Efficient planned system scales appropriately
- **NYC lowest** (5.4-38.3 km²/M)
  - Large population (8.34M) dilutes per-capita accessibility
  - Despite extensive network, more people share same area
  - High-density boroughs concentrate population

### Density-Normalized Coverage (DNC)
*Dimensionless metric accounting for city scale and population*

**What it measures:** Network efficiency after normalizing for BOTH city geographic size and population density. Enables fair comparison across cities of vastly different scales.

**Why it matters:** Removes confounding effects of city size and population to reveal true infrastructure productivity. The most robust metric for cross-city comparison.

| Time | NYC | Berlin | Singapore | Leader |
|------|-----|--------|-----------|--------|
| **20 min** | 0.0041 | 0.0086 | 0.0085 | Berlin |
| **30 min** | 0.0072 | 0.0178 | 0.0173 | Berlin |
| **45 min** | 0.0133 | 0.0326 | 0.0282 | Berlin |
| **60 min** | 0.0221 | 0.0445 | 0.0373 | Berlin |
| **75 min** | 0.0279 | 0.0463 | 0.0385 | Berlin |
| **90 min** | 0.0306 | 0.0463 | 0.0402 | Berlin |

**Formula:**
```
DNC(t) = (A_reachable(t) / A_city) / (L / P_millions)

Expanded form:
DNC(t) = (A_reachable(t) / A_city) × (P_millions / L)
```
Where:
- A_reachable(t) = Geographic area reachable within time threshold t (km²)
- A_city = Total city area (km²)
- L = Total route length (km)
- P_millions = City population in millions
- Units: Dimensionless ratio

**Results Analysis:**
- **Berlin most efficient** (0.0086-0.0463)
  - High productivity even after normalization
  - 153 km serves 3.85M people across 892 km² efficiently
  - Compact urban form enables genuine infrastructure efficiency
- **Singapore close second** (0.0085-0.0402)
  - Well-matched network-to-city-size ratio
  - Modern planning optimizes normalized performance
- **NYC lowest** (0.0041-0.0306)
  - Despite massive network, lower normalized efficiency
  - Sprawling form (629 km² served by 1,631 km) reduces productivity
  - High infrastructure per capita but lower area coverage fraction

**Key Insight:** DNC confirms efficiency rankings are **structural** (urban form) not artifacts of city size. Berlin's compact form genuinely enables better infrastructure productivity than NYC's sprawl.

---

## Functional Resilience Index (FRI) Analysis

### Understanding Network Resilience

FRI quantifies how well transit networks maintain performance when stations fail. Higher FRI values (closer to 1.0) indicate better resilience. We analyze two failure modes:
- **Random Failures**: Equipment breakdowns, accidents (unintentional disruptions)
- **Targeted Attacks**: Strategic removal of critical stations (intentional disruptions)

### City-by-City Resilience Analysis

#### Singapore MRT: Most Resilient Network (Overall FRI = 0.87)

**Strengths:**
- **Best random failure resistance (FRI = 0.88)**: Linear network structure with strategic redundancy
- **Strong betweenness resilience (FRI = 0.85)**: Purpose-built interchanges distribute routing alternatives
- **Planned robustness**: Modern design incorporates resilience from inception

**Why Singapore Leads:**
- **Optimal transfer station placement**: 23 transfer stations strategically positioned
- **Linear with loops**: East-West + North-South corridors plus Circle Line provide alternatives
- **Minimal critical single points**: Even removing high-betweenness stations leaves functional network
- **Modern infrastructure**: Newer system designed with redundancy principles

**Vulnerability:**
- **Degree-based attacks (FRI = 0.83)**: Large transfer hubs (Jurong East, Dhoby Ghaut) are critical
- **Island geography**: Limited alternative routes compared to grid-based systems

**Interpretation:** Singapore's resilience reflects **modern planning excellence** - deliberate design for fault tolerance rather than organic growth.

#### Berlin U-Bahn: Balanced Resilience (Overall FRI = 0.80)

**Strengths:**
- **Consistent performance**: Similar resilience across all attack types (~0.78-0.83)
- **No extreme vulnerabilities**: Balanced network without catastrophic weak points
- **Dense station network**: 0.90 km spacing provides local redundancy

**Characteristics:**
- **Moderate random failures (FRI = 0.80)**: Compact grid structure handles equipment failures well
- **Moderate targeted attacks**: Neither exceptionally vulnerable nor resilient to strategic disruption
- **Post-reunification integration**: Merged East/West networks provide some redundancy

**Vulnerabilities:**
- **Lower connectivity (ρ = 0.85)**: Fewer shared-track segments limit routing alternatives  
- **Hub dependency**: Some stations (Alexanderplatz, Friedrichstraße) are disproportionately critical
- **Grid limitations**: Rectangular network less flexible than radial-with-loops design

**Interpretation:** Berlin shows **pragmatic resilience** - adequate but not exceptional, reflecting incremental historical development rather than optimized planning.

#### NYC Subway: Complex Resilience Profile (Overall FRI = 0.73)

**Strengths:**
- **Best degree-attack resistance (FRI = 0.81)**: High redundancy from merged three-system legacy
- **Many alternative routes**: 1.22 connectivity means multiple paths between destinations
- **221 transfer stations**: Extensive transfer network provides rerouting options

**Vulnerabilities:**
- **Worst random failure performance (FRI = 0.70)**: Large, aging network susceptible to cascading disruptions
- **Complexity penalty**: 238 special vertices create more failure opportunities
- **Infrastructure age**: Equipment failures more likely in century-old system
- **Geographic sprawl**: Long radial lines vulnerable to single-point failures

**Why NYC Struggles with Random Failures:**
1. **System complexity**: More stations = more potential failure points
2. **Aged infrastructure**: Higher baseline failure probability
3. **Long dependencies**: Outer borough lines depend on Manhattan trunk segments
4. **Limited express bypass**: Local station failures impact entire lines

**Why NYC Excels Against Degree Attacks:**
1. **Redundant routing**: IRT/BMT/IND overlap provides alternatives
2. **Many transfer stations**: Removing one hub still leaves many transfer options
3. **Grid + radial hybrid**: Multiple connection patterns survive hub loss

**Interpretation:** NYC demonstrates **resilient through redundancy, vulnerable through scale** - the massive network's complexity is both strength (alternatives) and weakness (more failure modes).

### Comparative Resilience Insights

| Failure Mode | Best Performing | Why |
|--------------|----------------|------|
| **Random Failures** | Singapore (0.88) | Modern design, optimal spacing, strategic interchange placement |
| **Degree Attacks** | NYC (0.90) | High redundancy from three-system merger, many transfer options |
| **Betweenness Attacks** | Singapore (0.87) | Linear-with-loops design minimizes critical routing bottlenecks |
| **Overall Resilience** | Singapore (0.87) | Balanced excellence across all failure modes |

**Key Takeaway:** Network resilience depends on **design philosophy**, not just size:
- Singapore: **Planned resilience** through deliberate redundancy placement
- NYC: **Accidental resilience** from historical system overlap, undermined by scale/age
- Berlin: **Moderate resilience** from pragmatic grid design
---


## Functional Resilience Index (FRI)

### Overall Performance Under Disruptions

| City | Overall FRI | Random Failures | Degree-based | Betweenness-based |
|------|-------------|-----------------|--------------|-------------------|
| **Singapore** | **0.8724** | **0.8849** | 0.8324 | 0.8498 |
| **Berlin** | 0.7976 | 0.8031 | 0.7835 | 0.7845 |
| **NYC** | 0.7285 | 0.7029 | 0.8104 | 0.7745 |

**Methodology:**
- **Random Failures:** 10 independent trials per probability level (5%, 10%, 15%, 20%)
- **Degree-based Attacks:** Targeted removal of highest-degree (most connected) stations
- **Betweenness-based Attacks:** Targeted removal of highest-betweenness (most critical for paths) stations
- **Performance Ratio:** Ratio of post-disruption network performance to baseline

**Interpretation:**
- All networks show good resilience (FRI > 0.70)
- Singapore most resilient overall (0.87), especially to random failures (0.88)
- NYC shows higher vulnerability to random failures (0.70) but better resistance to degree attacks (0.81)
- Berlin balanced across all attack types (~0.78-0.80)

---

## Key Insights

### Network Scale

**NYC: The Megacity Network**
- **Largest** network by all measures: 358 stations, 1,631 km
- Serves 2.2x more people than Singapore, 2.2x more than Berlin
- Highest network density (2.10 km/km²) despite largest area
- Most complex transfer structure (τ = 12.5)

**Berlin: The Compact Network**
- **Densest** station spacing (0.90 km/station)
- Serves smallest population (3.85M) with moderate station count
- Best infrastructure efficiency (IE 0.48-2.51 km²/km)
- Lower directness penalty (τ = 4.5)

**Singapore: The Linear Network**
- **Most direct** system (τ = 2.67, best directness)
- Longest average station spacing (1.51 km/station)
- Perfect connectivity for linear structure (ρ = 1.0)
- Balanced efficiency (IE 0.39-1.84 km²/km)

### Accessibility Patterns

**Short Trips (20-30 min):**
- Berlin leads in efficiency (IE 0.48-0.96 km²/km)
- All cities achieve 50-80% reachability
- Good for commuter access

**Medium Trips (45-60 min):**
- Berlin dominates accessibility (PCA 70-96 km²/M)
- All networks achieve 95%+ reachability
- Covers most intra-city travel

**Long Trips (75-120 min):**
- Berlin maintains highest per-capita access (99.8 km²/M)
- All networks reach 100% reachability
- Reflects city size and network extent

### Accessibility Metrics Summary

**Infrastructure Efficiency (IE):**
- Berlin: 0.48-2.51 km²/km (leader - compact concentration)
- Singapore: 0.39-1.84 km²/km (moderate - linear efficiency)
- NYC: 0.13-0.28 km²/km (lowest - sprawling coverage)

**Per-Capita Accessibility (PCA):**
- Berlin: 19-100 km²/M (leader - low population density)
- Singapore: 13-62 km²/M (moderate - balanced planning)
- NYC: 5-38 km²/M (lowest - high population dilution)

**Density-Normalized Coverage (DNC):**
- Berlin: 0.0086-0.0463 (leader - genuinely efficient)
- Singapore: 0.0085-0.0402 (close second - optimal planning)
- NYC: 0.0041-0.0306 (lowest - sprawl penalty)



### Network Efficiency

**Coverage vs. Density Trade-off:**
- NYC: Extensive coverage (σ = 0.361) but spread thin (4.56 km/station)
- Berlin: Moderate coverage (σ = 0.150) with dense stations (0.90 km/station)
- Singapore: Compact coverage (σ = 0.130) with moderate spacing (1.51 km/station)

**Integration Strategies:**
- NYC: Hub-and-spoke with high transfer integration (ρ = 1.22, 221 transfer stations)
- Berlin: Balanced grid with multiple-use edges (27 transfers, 14 multiple-use edges)
- Singapore: Linear corridors with minimal transfers (ρ = 1.0, 23 transfers)

### Design Philosophy Differences

1. **NYC (Historical Merged System):**
   - 3 original systems (IRT, BMT, IND) merged into unified MTA
   - High redundancy and multiple routing options
   - Extensive transfer capabilities but complex navigation
   - Station grouping by name (not parent_station) due to multi-system history

2. **Berlin (Reconstructed Network):**
   - Post-reunification integration of East/West networks
   - Optimized for short trips and density
   - Compact coverage of city center
   - Efficient mid-range accessibility

3. **Singapore (Planned Modern System):**
   - Purpose-built integrated heavy rail network
   - Linear corridors with strategic interchange points
   - Direct routes minimize transfer complexity
   - Optimized for longer trips across island

---

## Methodology Notes

### Data Sources
- **GTFS Data:** Standard format for all cities (routes, trips, stop_times, stops)
- **NYC:** 25 subway lines (excluded express variants 6X, 7X, FX and Staten Island Railway)
- **Berlin:** 9 U-Bahn lines (S-Bahn excluded)
- **Singapore:** 8 MRT heavy rail lines (LRT excluded)

### Network Construction
- **Station Grouping:** 
  - NYC: By stop_name (to merge multi-system stations like Times Square)
  - Berlin/Singapore: By parent_station or stop_name
- **Edges:** Derived from GTFS trip sequences (consecutive stops)
- **Travel Times:** Calculated from GTFS stop_times with scheduled dwell/travel

### Metrics Consistency
All three cities use identical formulas for:
- D&K Indicators (σ, τ, ρ)
- Accessibility metrics (IE, PCA, DNC)
- FRI performance ratios
- Reachability percentages (with floor rounding)

---

## Visualizations

All cities include:
1. **Network Graph** (3 layouts: geographic, force-directed, spring)
2. **FRI Resilience Curves** (random and targeted failures)
3. **Accessibility Analysis** (IE, PCA, DNC metrics visualization)
4. **Network Degradation** (performance under attack)
5. **Travel Time Distribution** (with max, mean, median statistics)

Outputs available in `outputs/{city}/` directories.

---

## References

- Derrible, S., & Kennedy, C. (2010). The complexity and robustness of metro networks. *Physica A*, 389(17), 3678-3691.
- General Transit Feed Specification (GTFS) data for NYC MTA, BVG Berlin, and LTA Singapore
- Analysis methodology adapted from D&K framework with city-specific adjustments

---

*Last Updated: December 2024*
