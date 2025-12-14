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
| **City Area (A)** | 778.2 km² | 892 km² | 734.3 km² |

### Density Metrics

| Metric | NYC | Berlin | Singapore |
|--------|-----|--------|-----------|
| **Stations per Million** | 43 | 44 | 22 |
| **km per Station** | 4.56 | 0.90 | 1.51 |
| **km per 1000 people** | 0.196 | 0.040 | 0.034 |
| **Network Density** | 2.10 km/km² | 0.17 km/km² | 0.25 km/km² |

---

## Derrible & Kennedy Indicators

### Coverage (σ) - Network Size Indicator
*Captures network size relative to city area*

| City | σ | Interpretation |
|------|---|----------------|
| **NYC** | **0.361** | Extensive coverage (largest σ) |
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
| **NYC** | **326.7** | Highest usage prediction |
| **Berlin** | 222.4 | Moderate usage |
| **Singapore** | 221.3 | Moderate usage |

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

## System Level Mobility Efficiency (SME)

### SME Values by Time Threshold

| Time | NYC | Berlin | Singapore | Leader |
|------|-----|--------|-----------|--------|
| **20 min** | 1,047 | 2,663 | 2,743 | Singapore |
| **30 min** | 1,371 | 3,994 | 3,204 | Berlin |
| **45 min** | 1,840 | 7,772 | 6,204 | Berlin |
| **60 min** | 2,349 | 9,388 | 7,919 | Berlin |
| **75 min** | 2,364 | 9,459 | 8,020 | Berlin |
| **90 min** | 2,364 | 9,459 | 8,233 | Berlin |

### Reachability Percentage

| Time Threshold | NYC | Berlin | Singapore |
|----------------|-----|--------|-----------|
| **20 min** | 50.0% | 51.0% | 43.6% |
| **30 min** | 77.5% | 79.0% | 67.4% |
| **45 min** | 96.3% | 95.9% | 90.5% |
| **60 min** | 99.6% | 99.6% | 97.6% |
| **75 min** | 99.9% | 100.0% | 99.6% |
| **90 min** | 100.0% | 100.0% | 99.9% |
| **120 min** | 100.0% | 100.0% | 100.0% |

**Note:** Percentages are floored to 1 decimal place to avoid misleading rounding (99.99% displays as 99.9%, not 100.0%)

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
- Best SME performance at mid-to-long thresholds (45-90 min)
- Lower directness penalty (τ = 4.5)

**Singapore: The Linear Network**
- **Most direct** system (τ = 2.67, best directness)
- Longest average station spacing (1.51 km/station)
- Perfect connectivity for linear structure (ρ = 1.0)
- Best short-range SME (20 min threshold)

### Accessibility Patterns

**Short Trips (20-30 min):**
- Singapore leads in 20-min SME (2,743)
- All cities achieve 50-80% reachability
- Good for commuter access

**Medium Trips (45-60 min):**
- Berlin dominates (SME 7,772-9,388)
- All networks achieve 95%+ reachability
- Covers most intra-city travel

**Long Trips (75-120 min):**
- Berlin maintains lead
- All networks reach 100% reachability
- Reflects city size and network extent

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
- SME calculation (reachable area / normalized track length)
- FRI performance ratios
- Reachability percentages (with floor rounding)

---

## Visualizations

All cities include:
1. **Network Graph** (3 layouts: geographic, force-directed, spring)
2. **FRI Resilience Curves** (random and targeted failures)
3. **SME Analysis** (reachability % and SME values)
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
