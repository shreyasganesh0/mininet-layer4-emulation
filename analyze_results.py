#!/usr/bin/env python3
"""
Analysis Script for 5718 Protocol Study
Extracts 4 metrics: Throughput, Latency (RTT), Packet Loss, Jitter
"""

import json
import re
import os
import sys
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "experiment_results"

def parse_iperf_json(filepath):
    """
    Parse iperf3 JSON output
    Returns: dict with metrics
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        end = data.get('end', {})
        
        if 'sum_sent' in end:
            sent = end['sum_sent']
            received = end['sum_received']
            
            throughput_bps = received.get('bits_per_second', 0)
            throughput_mbps = throughput_bps / 1_000_000
            
            retransmits = sent.get('retransmits', 0)
            
            return {
                'throughput_mbps': throughput_mbps,
                'retransmits': retransmits,
                'protocol': 'TCP'
            }
        
        elif 'sum' in end:
            sum_data = end['sum']
            
            throughput_bps = sum_data.get('bits_per_second', 0)
            throughput_mbps = throughput_bps / 1_000_000
            
            jitter_ms = sum_data.get('jitter_ms', 0)
            lost_packets = sum_data.get('lost_packets', 0)
            total_packets = sum_data.get('packets', 0)
            loss_percent = sum_data.get('lost_percent', 0)
            
            return {
                'throughput_mbps': throughput_mbps,
                'jitter_ms': jitter_ms,
                'lost_packets': lost_packets,
                'total_packets': total_packets,
                'loss_percent': loss_percent,
                'protocol': 'UDP'
            }
        
        return None
        
    except Exception as e:
        print(f"  Error parsing {filepath}: {e}")
        return None

def parse_ping_output(filepath):
    """
    Parse ping output for latency and loss
    Returns: dict with metrics
    """
    try:
        with open(filepath, 'r') as f:
            output = f.read()
        
        loss_match = re.search(r'(\d+)% packet loss', output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0
        
        rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
        
        if rtt_match:
            rtt_min = float(rtt_match.group(1))
            rtt_avg = float(rtt_match.group(2))
            rtt_max = float(rtt_match.group(3))
            rtt_mdev = float(rtt_match.group(4))
            
            return {
                'packet_loss_percent': packet_loss,
                'rtt_min_ms': rtt_min,
                'rtt_avg_ms': rtt_avg,
                'rtt_max_ms': rtt_max,
                'rtt_mdev_ms': rtt_mdev
            }
        
        return {'packet_loss_percent': packet_loss}
        
    except Exception as e:
        print(f"  Error parsing {filepath}: {e}")
        return None

def analyze_results():
    """Analyze all result files and extract metrics"""
    
    print("\n" + "="*70)
    print("  ANALYZING RESULTS")
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

def plot_results(results):
    """Generate comparison plots"""
    
    print("\n" + "="*70)
    print("  GENERATING PLOTS")
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
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Protocol Performance Comparison ({mode.upper()} mode)', 
                 fontsize=16, fontweight='bold')
    
    ax = axes[0, 0]
    bars = ax.bar(range(len(labels)), metrics['throughput'], color='steelblue')
    ax.set_xlabel('Controller-Protocol')
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('1. Throughput Comparison')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=8)
    
    ax = axes[0, 1]
    bars = ax.bar(range(len(labels)), metrics['latency'], color='coral')
    ax.set_xlabel('Controller-Protocol')
    ax.set_ylabel('Round-Trip Time (ms)')
    ax.set_title('2. Latency Comparison')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=8)
    
    ax = axes[1, 0]
    bars = ax.bar(range(len(labels)), metrics['loss'], color='tomato')
    ax.set_xlabel('Controller-Protocol')
    ax.set_ylabel('Packet Loss (%)')
    ax.set_title('3. Packet Loss Comparison')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=8)
    
    ax = axes[1, 1]
    bars = ax.bar(range(len(labels)), metrics['jitter'], color='mediumseagreen')
    ax.set_xlabel('Controller-Protocol')
    ax.set_ylabel('Jitter (ms)')
    ax.set_title('4. Jitter Comparison (UDP only)')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:  
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    output_file = f"protocol_comparison_{mode}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved plot: {output_file}")
    
    plt.show()

def main():
    """Main analysis function"""
    
    results = analyze_results()
    
    if not results:
        print("\n✗ No results to analyze")
        return
    
    print_summary_table(results)
    
    try:
        plot_results(results)
        print("\n✓ Analysis complete!")
    except Exception as e:
        print(f"\n⚠ Could not generate plots: {e}")
        print("  Make sure matplotlib is installed: pip install matplotlib")

if __name__ == '__main__':
    main()
