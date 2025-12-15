"""
FRI Targeted Failures Comparison
Compares degree-based and betweenness-based attack resilience across NYC, Berlin, and Singapore
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

def load_targeted_failures(city_path, attack_type):
    """Load and filter targeted failure scenarios"""
    df = pd.read_csv(city_path)
    # Filter to specific attack type
    targeted_df = df[df['type'] == attack_type].copy()
    return targeted_df


def plot_combined_targeted_comparison(metric_type='transfers'):
    """
    Create combined comparison plot showing both degree and betweenness attacks
    Same color for same city, different line style for attack type
    
    Args:
        metric_type: 'transfers' or 'trains' - which delta interpretation to use
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    perf_col = f'performance_ratio_by_{metric_type}'
    
    # Line styles for attack types
    line_styles = {
        'degree': '-',       # Solid for degree
        'betweenness': '--'  # Dashed for betweenness
    }
    
    # Plot each city with both attack types
    for city_name, city_config in CITIES.items():
        try:
            # Plot degree attacks
            degree_df = load_targeted_failures(city_config['path'], 'degree')
            if len(degree_df) > 0 and perf_col in degree_df.columns:
                degree_df = degree_df.sort_values('failed_count')
                ax.plot(degree_df['failed_count'], degree_df[perf_col],
                       linewidth=2.5, 
                       color=city_config['color'], 
                       linestyle=line_styles['degree'],
                       alpha=0.9)
            
            # Plot betweenness attacks
            bet_df = load_targeted_failures(city_config['path'], 'betweenness')
            if len(bet_df) > 0 and perf_col in bet_df.columns:
                bet_df = bet_df.sort_values('failed_count')
                ax.plot(bet_df['failed_count'], bet_df[perf_col],
                       linewidth=2.5, 
                       color=city_config['color'], 
                       linestyle=line_styles['betweenness'],
                       alpha=0.9)
            
            print(f"✓ Loaded {city_name}: {len(degree_df)} degree + {len(bet_df)} betweenness scenarios")
        except Exception as e:
            print(f"✗ {city_name}: Error - {e}")
    
    # Baseline reference
    ax.axhline(y=1.0, color='gray', linestyle=':', linewidth=2, 
              alpha=0.6, zorder=0)
    
    # Styling
    ax.set_xlabel('Number of Stations Removed', fontsize=14, fontweight='bold')
    ax.set_ylabel('Performance Ratio', fontsize=14, fontweight='bold')
    ax.set_title(f'FRI Targeted Attacks Comparison',
                fontsize=16, fontweight='bold', pad=20)
    
    # Set x-axis
    ax.set_xlim([0.5, 8.5])
    ax.set_xticks(range(1, 9))
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    
    # Create custom legend with two sections
    from matplotlib.lines import Line2D
    
    # City legend entries (colors)
    city_handles = [
        Line2D([0], [0], color=CITIES['NYC']['color'], linewidth=2.5, label='NYC Subway'),
        Line2D([0], [0], color=CITIES['Berlin']['color'], linewidth=2.5, label='Berlin U-Bahn'),
        Line2D([0], [0], color=CITIES['Singapore']['color'], linewidth=2.5, label='Singapore MRT')
    ]
    
    # Attack type legend entries (line styles)
    attack_handles = [
        Line2D([0], [0], color='gray', linewidth=2.5, linestyle='-', label='Degree-Based'),
        Line2D([0], [0], color='gray', linewidth=2.5, linestyle='--', label='Betweenness-Based'),
        Line2D([0], [0], color='gray', linewidth=2, linestyle=':', label='Baseline', alpha=0.6)
    ]
    
    # Create two legends side by side
    legend1 = ax.legend(handles=city_handles, loc='center right', 
                       frameon=True, fancybox=True, shadow=False, 
                       framealpha=0.95, fontsize=11, title='City')
    ax.add_artist(legend1)  # Add first legend manually
    
    legend2 = ax.legend(handles=attack_handles, loc='upper right',
                       frameon=True, fancybox=True, shadow=False,
                       framealpha=0.95, fontsize=11, title='Attack Type')
    
    # Tight layout
    plt.tight_layout()
    
    # Save
    output_path = os.path.join(OUTPUT_DIR, f'fri_targeted_combined_{metric_type}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"\n✓ Saved combined targeted comparison ({metric_type}) to {output_path}")
    
    return output_path


def create_summary_table(attack_type='degree'):
    """Create summary statistics table for targeted attacks"""
    summary_data = []
    attack_label = 'Degree' if attack_type == 'degree' else 'Betweenness'
    
    for city_name, city_config in CITIES.items():
        try:
            targeted_df = load_targeted_failures(city_config['path'], attack_type)
            
            if len(targeted_df) > 0:
                # Calculate statistics
                overall_mean_transfers = targeted_df['performance_ratio_by_transfers'].mean()
                overall_mean_trains = targeted_df['performance_ratio_by_trains'].mean()
                
                # failed_count=5 specifically (typical midpoint)
                k5 = targeted_df[targeted_df['failed_count'] == 5]
                if len(k5) > 0:
                    mean_k5_transfers = k5['performance_ratio_by_transfers'].values[0]
                    mean_k5_trains = k5['performance_ratio_by_trains'].values[0]
                else:
                    mean_k5_transfers = None
                    mean_k5_trains = None
                
                summary_data.append({
                    'City': city_name,
                    f'Overall FRI ({attack_label}, transfers)': f"{overall_mean_transfers:.4f}",
                    f'Overall FRI ({attack_label}, trains)': f"{overall_mean_trains:.4f}",
                    f'FRI @ k=5 (transfers)': f"{mean_k5_transfers:.4f}" if mean_k5_transfers else 'N/A',
                    f'FRI @ k=5 (trains)': f"{mean_k5_trains:.4f}" if mean_k5_trains else 'N/A',
                    'Scenarios': len(targeted_df)
                })
        except Exception as e:
            print(f"Error processing {city_name}: {e}")
    
    summary_df = pd.DataFrame(summary_data)
    
    # Save to CSV
    output_path = os.path.join(OUTPUT_DIR, f'fri_{attack_type}_summary.csv')
    summary_df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved {attack_type} summary table to {output_path}")
    print(f"\n{attack_label}-Based Attack Summary:")
    print(summary_df.to_string(index=False))
    
    return summary_df


def main():
    """Generate combined targeted failure comparison plots and summaries"""
    print("=" * 80)
    print("FRI TARGETED FAILURES COMPARISON")
    print("=" * 80)
    print()
    
    # Create combined plots (both attack types on same plot)
    print("Creating combined targeted attack plots...")
    print("\n1. Using δ_transfers (line changes):")
    plot_combined_targeted_comparison(metric_type='transfers')
    
    print("\n2. Using δ_trains (train rides):")
    plot_combined_targeted_comparison(metric_type='trains')
    
    # Create summary tables
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    create_summary_table(attack_type='degree')
    print("\n" + "-" * 80)
    create_summary_table(attack_type='betweenness')
    
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
    print("\nGenerated plots:")
    print("  - outputs/comparison/fri_targeted_combined_transfers.png")
    print("  - outputs/comparison/fri_targeted_combined_trains.png")


if __name__ == "__main__":
    main()
