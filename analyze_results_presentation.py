#!/usr/bin/env python3
"""
analyze_results_presentation.py

Modified version of analyze_results.py that generates SEPARATE image files
for each metric - perfect for inserting into presentation slides.

Generates 4 files:
  - throughput_comparison.png
  - latency_comparison.png
  - packet_loss_comparison.png
  - jitter_comparison.png

Each file shows ALL protocols (unified comparison) for that one metric.

Usage:
    python3 analyze_results_presentation.py
"""

import json
import os
import re
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "experiment_results"

def parse_iperf_json(filepath):
    """Parse iperf3 JSON output file"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        result = {}
        
        # Extract throughput
        if 'end' in data and 'sum_received' in data['end']:
            bits_per_second = data['end']['sum_received'].get('bits_per_second', 0)
            result['throughput_mbps'] = bits_per_second / 1_000_000
        
        # Extract UDP-specific metrics
        if 'end' in data and 'sum' in data['end']:
            sum_data = data['end']['sum']
            
            # Jitter (UDP only)
            if 'jitter_ms' in sum_data:
                result['jitter_ms'] = sum_data['jitter_ms']
            
            # Packet loss (UDP only)
            if 'lost_percent' in sum_data:
                result['packet_loss_percent'] = sum_data['lost_percent']
        
        # Extract TCP retransmits
        if 'end' in data and 'sum_sent' in data['end']:
            result['retransmits'] = data['end']['sum_sent'].get('retransmits', 0)
        
        return result
    
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def parse_ping_output(filepath):
    """Parse ping output file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        result = {}
        
        # Extract RTT statistics
        rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', content)
        if rtt_match:
            result['rtt_min_ms'] = float(rtt_match.group(1))
            result['rtt_avg_ms'] = float(rtt_match.group(2))
            result['rtt_max_ms'] = float(rtt_match.group(3))
            result['rtt_mdev_ms'] = float(rtt_match.group(4))
        
        # Extract packet loss
        loss_match = re.search(r'(\d+)% packet loss', content)
        if loss_match:
            result['packet_loss_percent'] = float(loss_match.group(1))
        
        return result
    
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def analyze_results():
    """Load and analyze all experimental results"""
    
    print("\n" + "="*70)
    print("  ANALYZING EXPERIMENTAL RESULTS")
    print("="*70 + "\n")
    
    if not os.path.exists(RESULTS_DIR):
        print(f"✗ Results directory not found: {RESULTS_DIR}/")
        return None
    
    results = {}
    
    for filename in os.listdir(RESULTS_DIR):
        if not filename.endswith('_iperf.json'):
            continue
        
        parts = filename.replace('_iperf.json', '').split('_')
        if len(parts) < 3:
            continue
        
        controller = parts[0]  
        mode = parts[1]       
        protocol = parts[2]  
        
        print(f"Processing: {controller}/{mode}/{protocol}")
        
        if controller not in results:
            results[controller] = {}
        if mode not in results[controller]:
            results[controller][mode] = {}
        if protocol not in results[controller][mode]:
            results[controller][mode][protocol] = {}
        
        iperf_file = os.path.join(RESULTS_DIR, filename)
        iperf_data = parse_iperf_json(iperf_file)
        
        if iperf_data:
            results[controller][mode][protocol].update(iperf_data)
            print(f"  ✓ Throughput: {iperf_data.get('throughput_mbps', 0):.2f} Mbps")
        
        ping_filename = filename.replace('_iperf.json', '_ping.txt')
        ping_file = os.path.join(RESULTS_DIR, ping_filename)
        
        if os.path.exists(ping_file):
            ping_data = parse_ping_output(ping_file)
            if ping_data:
                results[controller][mode][protocol].update(ping_data)
                print(f"  ✓ RTT avg: {ping_data.get('rtt_avg_ms', 0):.2f} ms, "
                      f"Loss: {ping_data.get('packet_loss_percent', 0):.1f}%")
        
        print()
    
    return results

def print_summary_table(results):
    """Print a summary table of all results"""
    
    print("\n" + "="*70)
    print("  RESULTS SUMMARY")
    print("="*70 + "\n")
    
    for controller in sorted(results.keys()):
        print(f"\nController: {controller.upper()}")
        print("-" * 70)
        
        for mode in sorted(results[controller].keys()):
            print(f"\n  Mode: {mode.upper()}")
            print(f"  {'Protocol':<10} {'Throughput':<15} {'RTT Avg':<12} {'Loss %':<10} {'Jitter'}")
            print(f"  {'-'*10} {'-'*15} {'-'*12} {'-'*10} {'-'*10}")
            
            for protocol in ['reno', 'cubic', 'udp']:
                if protocol not in results[controller][mode]:
                    continue
                
                data = results[controller][mode][protocol]
                
                throughput = data.get('throughput_mbps', 0)
                rtt = data.get('rtt_avg_ms', 0)
                loss = data.get('packet_loss_percent', 0)
                jitter = data.get('jitter_ms', 0)
                
                print(f"  {protocol:<10} {throughput:>10.2f} Mbps  {rtt:>8.2f} ms  "
                      f"{loss:>7.1f} %  {jitter:>8.2f} ms")

def plot_individual_graphs(results):
    """Generate SEPARATE comparison plots for each metric - for presentation slides"""
    
    print("\n" + "="*70)
    print("  GENERATING INDIVIDUAL PRESENTATION GRAPHS")
    print("="*70 + "\n")
    
    mode = 'bottleneck'
    
    has_bottleneck = False
    for controller in results.keys():
        if mode in results[controller]:
            has_bottleneck = True
            break
    
    if not has_bottleneck:
        print("⚠ No bottleneck mode results found. Using debug mode.")
        mode = 'debug'
    
    protocols = ['reno', 'cubic', 'udp']
    controllers = sorted(results.keys())
    
    # Collect data
    metrics = {
        'throughput': [],
        'latency': [],
        'loss': [],
        'jitter': []
    }
    
    labels = []
    
    for controller in controllers:
        if mode not in results[controller]:
            continue
        
        for protocol in protocols:
            if protocol not in results[controller][mode]:
                continue
            
            data = results[controller][mode][protocol]
            
            labels.append(f"{controller}-{protocol}")
            metrics['throughput'].append(data.get('throughput_mbps', 0))
            metrics['latency'].append(data.get('rtt_avg_ms', 0))
            metrics['loss'].append(data.get('packet_loss_percent', 0))
            metrics['jitter'].append(data.get('jitter_ms', 0) if protocol == 'udp' else 0)
    
    if not labels:
        print("✗ No data to plot")
        return
    
    # Create color palette
    colors = {
        'throughput': 'steelblue',
        'latency': 'coral',
        'loss': 'tomato',
        'jitter': 'mediumseagreen'
    }
    
    # -----------------------------------------------------------------
    # GRAPH 1: Throughput
    # -----------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), metrics['throughput'], color=colors['throughput'])
    plt.xlabel('Controller-Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Throughput (Mbps)', fontsize=12, fontweight='bold')
    plt.title('Throughput Comparison', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_file = "throughput_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # -----------------------------------------------------------------
    # GRAPH 2: Latency
    # -----------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), metrics['latency'], color=colors['latency'])
    plt.xlabel('Controller-Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Round-Trip Time (ms)', fontsize=12, fontweight='bold')
    plt.title('Latency Comparison', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_file = "latency_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # -----------------------------------------------------------------
    # GRAPH 3: Packet Loss
    # -----------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), metrics['loss'], color=colors['loss'])
    plt.xlabel('Controller-Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Packet Loss (%)', fontsize=12, fontweight='bold')
    plt.title('Packet Loss Comparison', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_file = "packet_loss_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # -----------------------------------------------------------------
    # GRAPH 4: Jitter
    # -----------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), metrics['jitter'], color=colors['jitter'])
    plt.xlabel('Controller-Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Jitter (ms)', fontsize=12, fontweight='bold')
    plt.title('Jitter Comparison (UDP only)', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:  # Only show label for non-zero values
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_file = "jitter_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    print("\n" + "="*70)
    print("  ALL GRAPHS GENERATED SUCCESSFULLY")
    print("="*70)
    print("\nGenerated files:")
    print("  1. throughput_comparison.png  → Insert into Slide 6")
    print("  2. latency_comparison.png     → Insert into Slide 7")
    print("  3. packet_loss_comparison.png → Insert into Slide 8")
    print("  4. jitter_comparison.png      → Insert into Slide 9")
    print("\nEach graph shows ALL protocols (unified comparison) ✅")
    print("="*70 + "\n")

def main():
    """Main analysis function"""
    
    results = analyze_results()
    
    if not results:
        print("\n✗ No results to analyze")
        return
    
    print_summary_table(results)
    plot_individual_graphs(results)

if __name__ == "__main__":
    main()
