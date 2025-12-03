#!/usr/bin/env python3
"""
analyze_results_presentation.py - POX Results Only (FULLY FIXED)

Generates 4 separate graphs for presentation slides:
  - throughput_comparison.png
  - latency_comparison.png
  - packet_loss_comparison.png
  - jitter_comparison.png

"""

import json
import os
import re
import matplotlib.pyplot as plt

RESULTS_DIR = "experiment_results"

def parse_iperf_json(filepath):
    """
    Parse iperf3 JSON output
    Returns dict with all available metrics
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        result = {}
        
        # TCP uses sum_received for throughput
        if 'end' in data and 'sum_received' in data['end']:
            bits_per_second = data['end']['sum_received'].get('bits_per_second', 0)
            result['throughput_mbps'] = bits_per_second / 1_000_000
            result['protocol_type'] = 'TCP'
        
        # UDP uses sum for all metrics
        if 'end' in data and 'sum' in data['end']:
            sum_data = data['end']['sum']
            
            # UDP throughput (if not already set by TCP's sum_received)
            if 'throughput_mbps' not in result and 'bits_per_second' in sum_data:
                result['throughput_mbps'] = sum_data['bits_per_second'] / 1_000_000
                result['protocol_type'] = 'UDP'
            
            # UDP-specific metrics
            if 'jitter_ms' in sum_data:
                result['jitter_ms'] = sum_data['jitter_ms']
            
            # CRITICAL: UDP packet loss from iperf3 (e.g., 75%)
            # This should NOT be overwritten by ping's loss (0%)
            if 'lost_percent' in sum_data:
                result['iperf_packet_loss_percent'] = sum_data['lost_percent']
        
        return result
    
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON decode error in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Error parsing {filepath}: {e}")
        return None

def parse_ping_output(filepath):
    """
    Parse ping output for latency and packet loss
    Returns dict with ping metrics
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        result = {}
        
        # Extract RTT (round-trip time)
        rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', content)
        if rtt_match:
            result['rtt_min_ms'] = float(rtt_match.group(1))
            result['rtt_avg_ms'] = float(rtt_match.group(2))
            result['rtt_max_ms'] = float(rtt_match.group(3))
            result['rtt_mdev_ms'] = float(rtt_match.group(4))
        
        # Extract ping packet loss (ICMP)
        # Note: This is different from UDP's iperf3 packet loss
        loss_match = re.search(r'(\d+)% packet loss', content)
        if loss_match:
            result['ping_packet_loss_percent'] = float(loss_match.group(1))
        
        return result
    
    except Exception as e:
        print(f"  ✗ Error parsing {filepath}: {e}")
        return None

def analyze_results():
    """
    Load and analyze POX experimental results only
    Properly handles UDP vs TCP packet loss sources
    """
    
    print("\n" + "="*70)
    print("  ANALYZING POX RESULTS")
    print("="*70 + "\n")
    
    if not os.path.exists(RESULTS_DIR):
        print(f"✗ Results directory not found: {RESULTS_DIR}/")
        return None
    
    results = {}
    
    for filename in os.listdir(RESULTS_DIR):
        if not filename.endswith('_iperf.json'):
            continue
        
        # Skip non-POX results
        if not filename.startswith('pox_'):
            continue
        
        parts = filename.replace('_iperf.json', '').split('_')
        if len(parts) < 3:
            print(f"⚠ Skipping malformed filename: {filename}")
            continue
        
        controller = parts[0]  # pox
        mode = parts[1]        # bottleneck or debug
        protocol = parts[2]    # reno, cubic, udp
        
        print(f"Processing: {controller}/{mode}/{protocol}")
        
        # Initialize nested dict structure
        if controller not in results:
            results[controller] = {}
        if mode not in results[controller]:
            results[controller][mode] = {}
        if protocol not in results[controller][mode]:
            results[controller][mode][protocol] = {}
        
        # Parse iperf3 data
        iperf_file = os.path.join(RESULTS_DIR, filename)
        iperf_data = parse_iperf_json(iperf_file)
        
        if iperf_data:
            results[controller][mode][protocol].update(iperf_data)
            throughput = iperf_data.get('throughput_mbps', 0)
            print(f"  ✓ Throughput: {throughput:.2f} Mbps")
            
            # Show UDP-specific metrics
            if protocol == 'udp':
                if 'iperf_packet_loss_percent' in iperf_data:
                    loss = iperf_data['iperf_packet_loss_percent']
                    print(f"  ✓ UDP Packet Loss (iperf3): {loss:.2f}%")
                if 'jitter_ms' in iperf_data:
                    jitter = iperf_data['jitter_ms']
                    print(f"  ✓ Jitter: {jitter:.2f} ms")
        else:
            print(f"  ✗ Failed to parse iperf data")
        
        # Parse ping data
        ping_filename = filename.replace('_iperf.json', '_ping.txt')
        ping_file = os.path.join(RESULTS_DIR, ping_filename)
        
        if os.path.exists(ping_file):
            ping_data = parse_ping_output(ping_file)
            
            if ping_data:
                # Add RTT data
                if 'rtt_avg_ms' in ping_data:
                    results[controller][mode][protocol]['rtt_avg_ms'] = ping_data['rtt_avg_ms']
                    print(f"  ✓ RTT avg: {ping_data['rtt_avg_ms']:.2f} ms")
                
                # CRITICAL: Handle packet loss carefully
                # - For TCP: Use ping's packet loss (TCP iperf3 doesn't report loss)
                # - For UDP: Use iperf3's packet loss (NOT ping's 0%)
                if protocol != 'udp':
                    # TCP protocols: use ping packet loss
                    if 'ping_packet_loss_percent' in ping_data:
                        results[controller][mode][protocol]['packet_loss_percent'] = ping_data['ping_packet_loss_percent']
                        print(f"  ✓ Packet Loss (ping): {ping_data['ping_packet_loss_percent']:.1f}%")
                else:
                    # UDP: use iperf3 packet loss, ignore ping
                    if 'iperf_packet_loss_percent' in results[controller][mode][protocol]:
                        results[controller][mode][protocol]['packet_loss_percent'] = \
                            results[controller][mode][protocol]['iperf_packet_loss_percent']
                    if 'ping_packet_loss_percent' in ping_data:
                        print(f"  ℹ Ping Loss: {ping_data['ping_packet_loss_percent']:.1f}% (not used, using iperf3 loss)")
            else:
                print(f"  ✗ Failed to parse ping data")
        else:
            print(f"  ⚠ Ping file not found: {ping_filename}")
        
        print()
    
    return results

def generate_graphs(results):
    """
    Generate 4 separate graphs for POX results
    All graphs now use correct data sources
    """
    
    print("\n" + "="*70)
    print("  GENERATING PRESENTATION GRAPHS")
    print("="*70 + "\n")
    
    # Use bottleneck mode, fall back to debug if not available
    mode = 'bottleneck'
    if 'pox' not in results or mode not in results['pox']:
        mode = 'debug'
        print(f"⚠  Using debug mode data")
    
    if 'pox' not in results or mode not in results['pox']:
        print("✗ No POX data found")
        return
    
    protocols = ['reno', 'cubic', 'udp']
    data = results['pox'][mode]
    
    # Collect metrics
    labels = []
    throughput = []
    latency = []
    loss = []
    jitter = []
    
    for protocol in protocols:
        if protocol not in data:
            print(f"⚠ Warning: No data for {protocol}")
            continue
        
        labels.append(protocol.upper())
        throughput.append(data[protocol].get('throughput_mbps', 0))
        latency.append(data[protocol].get('rtt_avg_ms', 0))
        loss.append(data[protocol].get('packet_loss_percent', 0))
        jitter.append(data[protocol].get('jitter_ms', 0) if protocol == 'udp' else 0)
    
    if not labels:
        print("✗ No data to plot")
        return
    
    print(f"Plotting data for: {', '.join(labels)}")
    print(f"  Throughput: {[f'{t:.2f}' for t in throughput]} Mbps")
    print(f"  Latency: {[f'{l:.2f}' for l in latency]} ms")
    print(f"  Packet Loss: {[f'{p:.2f}' for p in loss]} %")
    print(f"  Jitter: {[f'{j:.2f}' for j in jitter]} ms\n")
    
    # Graph 1: Throughput
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), throughput, color='steelblue')
    plt.xlabel('Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Throughput (Mbps)', fontsize=12, fontweight='bold')
    plt.title('Throughput Comparison (POX Controller)', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels)
    plt.grid(axis='y', alpha=0.3)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig("throughput_comparison.png", dpi=300, bbox_inches='tight')
    print("✓ Saved: throughput_comparison.png")
    plt.close()
    
    # Graph 2: Latency
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), latency, color='coral')
    plt.xlabel('Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Round-Trip Time (ms)', fontsize=12, fontweight='bold')
    plt.title('Latency Comparison (POX Controller)', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels)
    plt.grid(axis='y', alpha=0.3)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig("latency_comparison.png", dpi=300, bbox_inches='tight')
    print("✓ Saved: latency_comparison.png")
    plt.close()
    
    # Graph 3: Packet Loss
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), loss, color='tomato')
    plt.xlabel('Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Packet Loss (%)', fontsize=12, fontweight='bold')
    plt.title('Packet Loss Comparison (POX Controller)', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels)
    plt.grid(axis='y', alpha=0.3)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig("packet_loss_comparison.png", dpi=300, bbox_inches='tight')
    print("✓ Saved: packet_loss_comparison.png")
    plt.close()
    
    # Graph 4: Jitter
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(labels)), jitter, color='mediumseagreen')
    plt.xlabel('Protocol', fontsize=12, fontweight='bold')
    plt.ylabel('Jitter (ms)', fontsize=12, fontweight='bold')
    plt.title('Jitter Comparison - UDP Only (POX Controller)', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(range(len(labels)), labels)
    plt.grid(axis='y', alpha=0.3)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig("jitter_comparison.png", dpi=300, bbox_inches='tight')
    print("✓ Saved: jitter_comparison.png")
    plt.close()
    
    print("\n" + "="*70)
    print("  ALL GRAPHS GENERATED SUCCESSFULLY")
    print("="*70)
    print("\nInsert these into your presentation slides:")
    print("  • throughput_comparison.png → Slide 6")
    print("  • latency_comparison.png → Slide 7")
    print("  • packet_loss_comparison.png → Slide 8")
    print("  • jitter_comparison.png → Slide 9")
    print()

def main():
    """Main analysis function"""
    
    results = analyze_results()
    
    if not results:
        print("\n✗ No results to analyze")
        print("\nMake sure you have run experiments first:")
        print("  sudo python3 run_clean_experiments.py")
        return
    
    # Check if we have any protocol data
    has_data = False
    if 'pox' in results:
        for mode in results['pox'].values():
            if mode:
                has_data = True
                break
    
    if not has_data:
        print("\n✗ No protocol data found")
        print("\nRun experiments with:")
        print("  sudo python3 run_clean_experiments.py")
        return
    
    generate_graphs(results)
    print("✓ Analysis complete!\n")

if __name__ == "__main__":
    main()
