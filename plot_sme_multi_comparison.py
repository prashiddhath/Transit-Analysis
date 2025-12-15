#!/usr/bin/env python3
"""
Multi-Metric SME Comparison Plotter

Creates comparison plots for all 4 SME metrics across cities.

Usage:
    python plot_sme_multi_comparison.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Define cities (excluding Singapore 2009)
CITIES = {
    'nyc': 'New York City',
    'berlin': 'Berlin',
    'singapore': 'Singapore'
}

# Color scheme
CITY_COLORS = {
    'nyc': '#1f77b4',        # Deep blue
    'berlin': '#ff7f0e',     # Warm orange
    'singapore': '#2ca02c'   # Vibrant green
}

def load_sme_data():
    """Load SME data from all cities"""
    print("Loading SME data from all cities...")
    
    sme_data = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define markers for each city
    city_markers = {
        'nyc': 'o',          # Circle
        'berlin': 's',       # Square
        'singapore': '^'     # Triangle
    }
    
    for city_id, city_name in CITIES.items():
        csv_path = os.path.join(base_dir, 'outputs', city_id, 'sme_results.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            sme_data[city_id] = {
                'name': city_name,
                'data': df,
                'color': CITY_COLORS[city_id],
                'marker': city_markers[city_id],
                'label': city_name
            }
            print(f"  ✓ Loaded {city_name}: {len(df)} time thresholds")
        else:
            print(f"  ✗ Missing: {csv_path}")
    
    return sme_data


def plot_metric_comparison(sme_data, metric_name, ylabel, title, output_path, decimal_places=2):
    """Create comparison plot for a single metric"""
    # Find common time thresholds
    all_thresholds = [set(city_info['data']['time_threshold'].values) 
                      for city_info in sme_data.values()]
    common_thresholds = sorted(list(set.intersection(*all_thresholds)))
    
    # Prepare data
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(common_thresholds))
    width = 0.2
    
    # Plot bars for each city
    for i, (city_id, city_info) in enumerate(sme_data.items()):
        df = city_info['data']
        df_filtered = df[df['time_threshold'].isin(common_thresholds)].sort_values('time_threshold')
        values = df_filtered[metric_name].values
        
        offset = (i - len(sme_data)/2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, 
                     label=city_info['name'],
                     color=city_info['color'],
                     alpha=0.85,
                     edgecolor='black',
                     linewidth=1.2)
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            format_str = f'{{:.{decimal_places}f}}'
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   format_str.format(val),
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Customize plot
    ax.set_xlabel('Time Threshold (minutes)', fontsize=16, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=16, fontweight='bold')
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{t} min' for t in common_thresholds], fontsize=14)
    ax.tick_params(axis='y', labelsize=14)
    ax.legend(loc='upper left', fontsize=13, frameon=True, 
             facecolor='white', edgecolor='gray', framealpha=0.95)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved {metric_name} comparison to: {output_path}")


def create_3panel_comparison(sme_data, output_path='outputs/comparison/efficiency_all_metrics.png'):
    """Create 3-panel horizontal comparison showing IE, PCA, and DNC metrics"""
    # Find common time thresholds
    all_thresholds = [set(city_info['data']['time_threshold'].values) 
                     for city_info in sme_data.values()]
    common_thresholds = sorted(list(set.intersection(*all_thresholds)))
    
    # Create 1x3 subplot
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    # Define metrics to plot (removed Legacy SME)
    metrics = [
        ('infrastructure_efficiency', 'Infrastructure Efficiency\n(km²/track-km)', 'IE'),
        ('per_capita_accessibility', 'Per-Capita Accessibility\n(km²/M people)', 'PCA'),
        ('density_normalized_coverage', 'Density-Normalized Coverage', 'DNC')
    ]
    
    # Plot each metric
    for idx, (metric_key, metric_label, metric_short) in enumerate(metrics):
        ax = axes[idx]
        
        # Plot each city
        for city_id, city_info in sme_data.items():
            city_data = city_info['data']
            # Filter to common thresholds and sort
            filtered_data = city_data[city_data['time_threshold'].isin(common_thresholds)].copy()
            filtered_data = filtered_data.sort_values('time_threshold')
            
            ax.plot(filtered_data['time_threshold'], 
                   filtered_data[metric_key],
                   marker=city_info['marker'],
                   color=city_info['color'],
                   linewidth=2.5,
                   markersize=10,
                   label=city_info['label'],
                   alpha=0.9)
        
        # Styling
        ax.set_xlabel('Time Threshold (minutes)', fontsize=11, fontweight='bold')
        ax.set_ylabel(metric_label, fontsize=11, fontweight='bold')
        ax.set_title(f'{metric_short}', fontsize=13, fontweight='bold', pad=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xticks(common_thresholds)
        
        # Only show legend on first plot
        if idx == 0:
            ax.legend(fontsize=10, loc='best', frameon=True, 
                     fancybox=True, shadow=True, framealpha=0.95)
    
    # No main title
    plt.tight_layout()
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Saved 3-panel comparison to: {output_path}")


def main():
    print("\n" + "=" * 80)
    print("MULTI-METRIC SME COMPARISON")
    print("=" * 80)
    
    # Load data
    sme_data = load_sme_data()
    
    if not sme_data:
        print("\nERROR: No SME data found!")
        return
    
    print("\nGenerating comparison plots...")
    
    # Create individual metric plots
    plot_metric_comparison(
        sme_data,
        'per_capita_accessibility',
        'Per-Capita Accessibility (km²/M people)',
        'Per-Capita Accessibility (PCA) Comparison\nAccessible Area per Million People',
        'outputs/comparison/pca_comparison.png',
        decimal_places=2
    )
    
    plot_metric_comparison(
        sme_data,
        'density_normalized_coverage',
        'Density-Normalized Coverage',
        'Density-Normalized Coverage (DNC) Comparison\nCoverage Fraction per Per-Capita Infrastructure',
        'outputs/comparison/dnc_comparison.png',
        decimal_places=4
    )
    
    plot_metric_comparison(
        sme_data,
        'sme_legacy',
        'Legacy SME (km²/track-km/M)',
        'Legacy SME Comparison\nOriginal Formula: A/(L×P)',
        'outputs/comparison/sme_legacy_comparison.png',
        decimal_places=2
    )
    
    # Create 3-panel comparison
    create_3panel_comparison(sme_data)
    
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
    print("\nGenerated plots:")
    print("  - outputs/comparison/pca_comparison.png")
    print("  - outputs/comparison/dnc_comparison.png")
    print("  - outputs/comparison/sme_legacy_comparison.png")
    print("  - outputs/comparison/sme_all_metrics.png (3-panel view)")


if __name__ == '__main__':
    main()
