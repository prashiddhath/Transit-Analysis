#!/usr/bin/env python3
"""
Standalone FRI Plot Generator

Reads pre-computed FRI scenarios from CSV files and generates dual FRI resilience plots.
This avoids re-running expensive network analysis.

Usage:
    python plot_fri_from_csv.py <city_name>
    
Example:
    python plot_fri_from_csv.py nyc
    python plot_fri_from_csv.py berlin
    python plot_fri_from_csv.py singapore
    python plot_fri_from_csv.py singapore_2009
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def plot_fri_resilience(scenarios_df, output_path, metric_type='transfers', city_name=''):
    """Generate FRI resilience plot with auto-scaling y-axis
    
    Args:
        scenarios_df: DataFrame with scenario results
        output_path: Path to save visualization
        metric_type: 'transfers' or 'trains' - which delta interpretation to use
        city_name: Name of city for title
    """
    # Select appropriate performance ratio column
    perf_col = f'performance_ratio_by_{metric_type}'
    
    if perf_col not in scenarios_df.columns:
        print(f"ERROR: Column '{perf_col}' not found in scenarios DataFrame!")
        print(f"Available columns: {list(scenarios_df.columns)}")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Random failures
    random_data = scenarios_df[scenarios_df['type'] == 'random'].copy()
    if len(random_data) > 0:
        grouped = random_data.groupby('prob')[perf_col].agg(['mean', 'std'])
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
        
        # Auto-scale y-axis with some padding
        y_min = (grouped['mean'] - grouped['std']).min()
        y_max = max((grouped['mean'] + grouped['std']).max(), 1.0)
        y_padding = (y_max - y_min) * 0.1
        ax1.set_ylim([max(0, y_min - y_padding), y_max + y_padding])
    
    # Plot 2: Targeted failures
    colors = {'degree': '#4ECDC4', 'betweenness': '#FFD93D'}
    all_values = []
    
    for scenario_type in ['degree', 'betweenness']:
        targeted_data = scenarios_df[scenarios_df['type'] == scenario_type].copy()
        if len(targeted_data) > 0:
            grouped = targeted_data.groupby('failed_count')[perf_col].mean()
            color = colors[scenario_type]
            ax2.plot(grouped.index, grouped.values, marker='o', linewidth=2, 
                    markersize=8, label=scenario_type.capitalize(), color=color)
            all_values.extend(grouped.values)
    
    if all_values:
        ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Baseline')
        ax2.set_xlabel('Number of Stations Removed', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Performance Ratio', fontsize=12, fontweight='bold')
        ax2.set_title('Targeted Station Failures', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=10)
        
        # Auto-scale y-axis with some padding
        y_min = min(all_values)
        y_max = max(max(all_values), 1.0)
        y_padding = (y_max - y_min) * 0.1
        ax2.set_ylim([max(0, y_min - y_padding), y_max + y_padding])
    
    title = f'Functional Resilience Index (FRI) - Using δ_{metric_type}'
    if city_name:
        title = f'{city_name.upper()} - {title}'
    
    plt.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_fri_from_csv.py <city_name>")
        print("\nAvailable cities: nyc, berlin, singapore, singapore_2009")
        sys.exit(1)
    
    city = sys.argv[1].lower()
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(base_dir, 'outputs', city, 'fri_scenarios.csv')
    output_dir = os.path.join(base_dir, 'outputs', city)
    
    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"ERROR: File not found: {input_csv}")
        print(f"\nMake sure you've run the {city}_network_metrics.py script first!")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"FRI Plot Generator - {city.upper()}")
    print(f"{'='*60}")
    print(f"\nReading scenarios from: {input_csv}")
    
    # Load scenarios
    scenarios_df = pd.read_csv(input_csv)
    print(f"Loaded {len(scenarios_df)} scenarios")
    
    # Check for required columns
    required_cols = ['type', 'performance_ratio_by_transfers', 'performance_ratio_by_trains']
    missing_cols = [col for col in required_cols if col not in scenarios_df.columns]
    
    if missing_cols:
        print(f"\nERROR: Missing required columns: {missing_cols}")
        print(f"Available columns: {list(scenarios_df.columns)}")
        print(f"\nThe scenarios CSV may be from an old run. Please re-run {city}_network_metrics.py")
        sys.exit(1)
    
    # Display data summary
    print(f"\nScenario types:")
    print(scenarios_df.groupby('type').size())
    
    # Check performance ratio ranges
    print(f"\nPerformance Ratio Ranges:")
    for metric in ['transfers', 'trains']:
        col = f'performance_ratio_by_{metric}'
        print(f"  {metric:10s}: {scenarios_df[col].min():.4f} to {scenarios_df[col].max():.4f}")
    
    # Generate plots
    print(f"\nGenerating FRI plots...")
    
    # Plot 1: Using transfers interpretation
    output_path_transfers = os.path.join(output_dir, f'fri_transfers_{city}.png')
    plot_fri_resilience(scenarios_df, output_path_transfers, 
                       metric_type='transfers', city_name=city)
    
    # Plot 2: Using trains interpretation
    output_path_trains = os.path.join(output_dir, f'fri_trains_{city}.png')
    plot_fri_resilience(scenarios_df, output_path_trains, 
                       metric_type='trains', city_name=city)
    
    print(f"\n{'='*60}")
    print(f"FRI plots generated successfully!")
    print(f"{'='*60}")
    print(f"\nOutput files:")
    print(f"  - {output_path_transfers}")
    print(f"  - {output_path_trains}")
    print()


if __name__ == '__main__':
    main()
