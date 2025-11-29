#!/usr/bin/env python3
"""
LIVE DEMO: TCP Reno Performance Test
Shows real-time output suitable for presentation
"""

import os
import sys
import time
from functools import partial
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from simple_dumbbell import SimpleDumbbellTopo

def print_banner(text):
    """Print a nice banner"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_section(text):
    """Print a section header"""
    print("\n" + "─"*70)
    print(f"  {text}")
    print("─"*70 + "\n")

def main():
    """Run TCP Reno demo"""
    
    print_banner("LIVE DEMO: TCP RENO PERFORMANCE TEST")
    
    # Ask for controller and mode
    print("Which controller are you using?")
    print("  1) POX (OpenFlow 1.0)")
    print("  2) Ryu (OpenFlow 1.3)")
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == '1':
        controller_name = 'pox'
        print("\n→ Using POX controller (OpenFlow 1.0)")
    elif choice == '2':
        controller_name = 'ryu'
        print("\n→ Using Ryu controller (OpenFlow 1.3)")
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\nWhich mode?")
    print("  1) Debug mode (High-speed link)")
    print("  2) Project mode (10Mbps bottleneck)")
    mode_choice = input("\nEnter 1 or 2: ").strip()
    
    if mode_choice == '1':
        use_bottleneck = False
        print("\n→ Using DEBUG mode (1Gbps link)")
    elif mode_choice == '2':
        use_bottleneck = True
        print("\n→ Using PROJECT mode (10Mbps bottleneck, 50ms delay, 1% loss)")
    else:
        print("Invalid choice. Exiting.")
        return
    
    setLogLevel('info')
    
    print_section("STEP 1: Creating Network Topology")
    
    info("*** Building dumbbell topology...\n")
    topo = SimpleDumbbellTopo(use_bottleneck=use_bottleneck)
    
    if controller_name == 'ryu':
        info("*** Configuring switches for OpenFlow 1.3 (Ryu)\n")
        switch_class = partial(OVSSwitch, protocols='OpenFlow13')
    else:
        info("*** Configuring switches for OpenFlow 1.0 (POX)\n")
        switch_class = OVSSwitch
    
    net = Mininet(
        topo=topo,
        link=TCLink,
        controller=partial(RemoteController, ip='127.0.0.1', port=6633),
        switch=switch_class,
        autoSetMacs=True
    )
    
    try:
        info("*** Starting network\n")
        net.start()
        
        print_section("STEP 2: Waiting for Network Convergence")
        info("*** Waiting for switches to connect to controller")
        for i in range(20):
            info('.')
            time.sleep(1)
        info(' Done!\n')
        
        print_section("STEP 3: Testing Connectivity")
        
        client = net.get('h1')
        server = net.get('h13')
        
        info(f"*** Test path: {client.name} ({client.IP()}) → {server.name} ({server.IP()})\n")
        
        print("\n[Running: ping -c 3 10.0.0.13]")
        result = client.cmd('ping -c 3 -W 2 10.0.0.13')
        print(result)
        
        if '3 received' in result or '2 received' in result:
            print("✓ Connectivity OK\n")
        else:
            print("✗ Connectivity FAILED - Make sure controller is running!\n")
            return
        
        print_section("STEP 4: Starting iperf3 Server")
        
        server.cmd('pkill -9 iperf3')
        time.sleep(1)
        
        print(f"[Running on {server.name}: iperf3 -s]")
        server.cmd('iperf3 -s -D')
        time.sleep(2)
        print(f"✓ iperf3 server started on {server.IP()}\n")
        
        print_section("STEP 5: Running TCP Reno Performance Test")
        
        print("Protocol: TCP Reno")
        print("Congestion Control: Reno (classic AIMD)")
        print("Test Duration: 30 seconds")
        print("Command: iperf3 -c 10.0.0.13 -C reno -t 30\n")
        
        input("Press ENTER to start test...")
        print("\n" + "─"*70)
        print("  LIVE RESULTS")
        print("─"*70 + "\n")
        
        # Run iperf3 WITHOUT -J flag so we see live output
        output = client.cmd('iperf3 -c 10.0.0.13 -C reno -t 30')
        print(output)
        
        print("\n" + "─"*70)
        print("  TEST COMPLETE")
        print("─"*70 + "\n")
        
        # Also save JSON version for analysis
        print("Saving detailed results for analysis...")
        output_json = client.cmd('iperf3 -c 10.0.0.13 -C reno -t 5 -J')
        
        if not os.path.exists('experiment_results'):
            os.makedirs('experiment_results')
        
        mode = 'bottleneck' if use_bottleneck else 'debug'
        filename = f'experiment_results/{controller_name}_{mode}_reno_iperf.json'
        
        with open(filename, 'w') as f:
            f.write(output_json)
        
        print(f"✓ Detailed results saved to: {filename}\n")
        
        print_section("STEP 6: Measuring Latency with Ping")
        
        print("Running 20 pings to measure round-trip time...\n")
        print("[Running: ping -c 20 10.0.0.13]\n")
        
        ping_output = client.cmd('ping -c 20 -i 0.2 10.0.0.13')
        print(ping_output)
        
        # Save ping results
        ping_filename = f'experiment_results/{controller_name}_{mode}_reno_ping.txt'
        with open(ping_filename, 'w') as f:
            f.write(ping_output)
        
        print(f"\n✓ Ping results saved to: {ping_filename}\n")
        
        print_banner("TCP RENO DEMO COMPLETE")
        
        print("Key Observations:")
        print("  • TCP Reno uses classic AIMD (Additive Increase, Multiplicative Decrease)")
        print("  • Window grows linearly, halves on packet loss")
        print("  • Fast retransmit and fast recovery algorithms")
        print("  • Baseline congestion control for comparison\n")
        
        print("Next steps:")
        print("  1. Run demo for TCP CUBIC: sudo python3 demo_tcp_cubic.py")
        print("  2. Run demo for UDP: sudo python3 demo_udp.py")
        print("  3. Analyze all results: python3 analyze_results.py\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        info("\n*** Stopping network\n")
        net.stop()
        print("\n✓ Network stopped. Demo complete.\n")

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("This script must be run as root (use sudo)")
        sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
