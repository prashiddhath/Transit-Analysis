"""
FRI Random Failures Comparison
Compares random station failure resilience across NYC, Berlin, and Singapore
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# Output directory
OUTPUT_DIR = "outputs/comparison"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# City configurations
CITIES = {
    'NYC': {
        'path': 'outputs/nyc/fri_scenarios.csv',
        'color': '#E63946',
        'marker': 'o',
        'label': 'NYC Subway'
    },
    'Berlin': {
        'path': 'outputs/berlin/fri_scenarios.csv',
        'color': '#4ECDC4',
        'marker': 's',
        'label': 'Berlin U-Bahn'
    },
    'Singapore': {
        'path': 'outputs/singapore/fri_scenarios.csv',
        'color': '#FFB703',
        'marker': '^',
        'label': 'Singapore MRT'
    }
}

def load_random_failures(city_path):
    """Load and filter random failure scenarios"""
    df = pd.read_csv(city_path)
    # Filter to random failures only
    random_df = df[df['type'] == 'random'].copy()
    return random_df


def plot_random_failures_comparison(metric_type='transfers'):
    """
    Create comparison plot for random failures across all cities
    
    Args:
        metric_type: 'transfers' or 'trains' - which delta interpretation to use
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    perf_col = f'performance_ratio_by_{metric_type}'
    
    # Plot each city
    for city_name, city_config in CITIES.items():
        try:
            random_df = load_random_failures(city_config['path'])
            
            if len(random_df) > 0 and perf_col in random_df.columns:
                # Group by probability and calculate mean ± std
                grouped = random_df.groupby('prob')[perf_col].agg(['mean', 'std'])
                
                # Plot line with error bars
                ax.errorbar(grouped.index * 100, grouped['mean'], 
                           yerr=grouped['std'],
                           marker=city_config['marker'], 
                           linewidth=2.5, 
                           markersize=10, 
                           capsize=5,
                           color=city_config['color'], 
                           label=city_config['label'],
                           alpha=0.9)
                
                # Fill between for visual emphasis
                ax.fill_between(grouped.index * 100, 
                               grouped['mean'] - grouped['std'], 
                               grouped['mean'] + grouped['std'], 
                               alpha=0.15, 
                               color=city_config['color'])
                
                print(f"✓ Loaded {city_name}: {len(random_df)} scenarios")
            else:
                print(f"⚠ {city_name}: No data or missing column {perf_col}")
        except FileNotFoundError:
            print(f"✗ {city_name}: File not found - {city_config['path']}")
        except Exception as e:
            print(f"✗ {city_name}: Error - {e}")
    
    # Baseline reference
    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=2, 
              alpha=0.6, label='Baseline (No Failures)', zorder=0)
    
    # Styling
    ax.set_xlabel('Failure Probability (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Performance Ratio', fontsize=14, fontweight='bold')
    ax.set_title(f'FRI Random Failures Comparison',
                fontsize=16, fontweight='bold', pad=20)
    
    # Set x-axis limits with padding
    ax.set_xlim([4, 21])
    ax.set_xticks([5, 10, 15, 20])
    
    # Grid and legend
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax.legend(fontsize=12, loc='best', frameon=True, fancybox=True, 
             shadow=True, framealpha=0.95)
    
    # Tight layout
    plt.tight_layout()
    
    # Save
    output_path = os.path.join(OUTPUT_DIR, f'fri_random_{metric_type}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"\n✓ Saved comparison plot to {output_path}")
    
    return output_path


def create_summary_table():
    """Create summary statistics table for random failures"""
    summary_data = []
    
    for city_name, city_config in CITIES.items():
        try:
            random_df = load_random_failures(city_config['path'])
            
            if len(random_df) > 0:
                # Calculate overall statistics
                overall_mean_transfers = random_df['performance_ratio_by_transfers'].mean()
                overall_mean_trains = random_df['performance_ratio_by_trains'].mean()
                
                # 20% failure rate specifically
                failure_20 = random_df[random_df['prob'] == 0.20]
                if len(failure_20) > 0:
                    mean_20_transfers = failure_20['performance_ratio_by_transfers'].mean()
                    mean_20_trains = failure_20['performance_ratio_by_trains'].mean()
                else:
                    mean_20_transfers = None
                    mean_20_trains = None
                
                summary_data.append({
                    'City': city_name,
                    'Overall FRI (transfers)': f"{overall_mean_transfers:.4f}",
                    'Overall FRI (trains)': f"{overall_mean_trains:.4f}",
                    'FRI @ 20% (transfers)': f"{mean_20_transfers:.4f}" if mean_20_transfers else 'N/A',
                    'FRI @ 20% (trains)': f"{mean_20_trains:.4f}" if mean_20_trains else 'N/A',
                    'Scenarios': len(random_df)
                })
        except Exception as e:
            print(f"Error processing {city_name}: {e}")
    
    summary_df = pd.DataFrame(summary_data)
    
    # Save to CSV
    output_path = os.path.join(OUTPUT_DIR, 'fri_random_summary.csv')
    summary_df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved summary table to {output_path}")
    print("\nSummary Statistics:")
    print(summary_df.to_string(index=False))
    
    return summary_df


def main():
    """Generate random failure comparison plots and summary"""
    print("=" * 80)
    print("FRI RANDOM FAILURES COMPARISON")
    print("=" * 80)
    print()
    
    # Create plots for both interpretations
    print("Creating comparison plots...")
    print("\n1. Using δ_transfers (line changes):")
    plot_random_failures_comparison(metric_type='transfers')
    
    print("\n2. Using δ_trains (train rides):")
    plot_random_failures_comparison(metric_type='trains')
    
    # Create summary table
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    create_summary_table()
    
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
