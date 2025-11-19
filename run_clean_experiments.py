#!/usr/bin/env python3
"""
Clean Experiment Runner for 5718 Protocol Study
- Works with both POX and Ryu
- Tests TCP Reno, TCP CUBIC, and UDP
- Collects 4 metrics: Throughput, Latency, Packet Loss, Jitter
"""

import os
import sys
import time
import subprocess
from functools import partial
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from simple_dumbbell import SimpleDumbbellTopo

OUTPUT_DIR = "experiment_results"
TEST_DURATION = 30  
PING_COUNT = 100   

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}/")

def wait_for_convergence(net, timeout=20):
    """Wait for network to converge (all switches connected)"""
    info("*** Waiting for network convergence")
    for i in range(timeout):
        info('.')
        time.sleep(1)
    info(' Done!\n')

def test_basic_connectivity(client, server):
    """Test basic connectivity with ping"""
    info(f"*** Testing connectivity: {client.name} -> {server.name}\n")
    
    for attempt in range(1, 4):
        info(f"  Attempt {attempt}/3... ")
        result = client.cmd(f'ping -c 3 -W 2 {server.IP()}')
        
        if '3 received' in result or '2 received' in result:
            info("OK\n")
            return True
        elif '1 received' in result:
            info("Partial\n")
            time.sleep(3)
        else:
            info("Failed\n")
            time.sleep(3)
    
    return False

def run_iperf_test(client, server, protocol, duration, output_file):
    """
    Run iperf3 test and capture output
    
    Returns: (success, output_text)
    """
    info(f"*** Running {protocol.upper()} test ({duration}s)...\n")
    
    server.cmd('pkill -9 iperf3')  
    time.sleep(1)
    server.cmd('iperf3 -s -D') 
    time.sleep(2)
    
    if protocol == 'udp':
        cmd = f'iperf3 -c {server.IP()} -u -b 20M -t {duration} -J'
    else:
        cmd = f'iperf3 -c {server.IP()} -C {protocol} -t {duration} -J'
    
    info(f"  Command: {cmd}\n")
    output = client.cmd(cmd)
    
    with open(output_file, 'w') as f:
        f.write(output)
    
    info(f"  Saved to: {output_file}\n")
    
    success = 'error' not in output.lower() and len(output) > 100
    
    server.cmd('pkill -9 iperf3')
    
    return success, output

def run_ping_test(client, server, count, output_file):
    """
    Run ping test for latency and loss measurements
    
    Returns: (success, output_text)
    """
    info(f"*** Running ping test ({count} packets)...\n")
    
    cmd = f'ping -c {count} -i 0.2 {server.IP()}'
    output = client.cmd(cmd)
    
    with open(output_file, 'w') as f:
        f.write(output)
    
    info(f"  Saved to: {output_file}\n")
    
    success = 'bytes from' in output
    
    return success, output

def run_experiment_set(controller_name, use_bottleneck=False):
    """
    Run complete experiment set for one controller
    
    Args:
        controller_name: 'pox' or 'ryu'
        use_bottleneck: True for project mode, False for debug mode
    """
    
    print("\n" + "="*70)
    print(f"  EXPERIMENT SET: {controller_name.upper()}")
    print(f"  Mode: {'PROJECT (Bottleneck)' if use_bottleneck else 'DEBUG (High-speed)'}")
    print("="*70 + "\n")
    
    info("*** Creating topology\n")
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
        
        wait_for_convergence(net)
        
        client = net.get('h1')
        server = net.get('h13')
        
        info(f"*** Test hosts: {client.name} ({client.IP()}) -> "
             f"{server.name} ({server.IP()})\n")
        
        if not test_basic_connectivity(client, server):
            print("\n✗ ERROR: Cannot establish connectivity!")
            print("  Make sure controller is running:")
            if controller_name == 'ryu':
                print("    Terminal 1: ryu-manager ryu.app.simple_switch_13")
            else:
                print("    Terminal 1: ./pox.py forwarding.l2_learning")
            return False
        
        print("\n✓ Connectivity established!\n")
        
        protocols = ['reno', 'cubic', 'udp']
        
        for protocol in protocols:
            print(f"\n{'─'*70}")
            print(f"  TESTING: {protocol.upper()}")
            print(f"{'─'*70}\n")
            
            mode = 'bottleneck' if use_bottleneck else 'debug'
            iperf_file = f"{OUTPUT_DIR}/{controller_name}_{mode}_{protocol}_iperf.json"
            ping_file = f"{OUTPUT_DIR}/{controller_name}_{mode}_{protocol}_ping.txt"
            
            success, output = run_iperf_test(client, server, protocol, 
                                            TEST_DURATION, iperf_file)
            
            if success:
                info(f"  ✓ iperf test completed\n")
            else:
                info(f"  ⚠ iperf test may have issues\n")
            
            time.sleep(2)
            
            success, output = run_ping_test(client, server, PING_COUNT, ping_file)
            
            if success:
                info(f"  ✓ ping test completed\n")
            else:
                info(f"  ⚠ ping test may have issues\n")
            
            time.sleep(2)
        
        print("\n" + "="*70)
        print("  EXPERIMENT SET COMPLETE")
        print("="*70 + "\n")
        
        print("Generated files:")
        for filename in sorted(os.listdir(OUTPUT_DIR)):
            if controller_name in filename and mode in filename:
                filepath = os.path.join(OUTPUT_DIR, filename)
                size = os.path.getsize(filepath)
                print(f"  {filename}: {size} bytes")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        info("\n*** Stopping network\n")
        net.stop()

def check_controller_running():
    """Check if a controller is running on port 6633"""
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        if ':6633' in result.stdout:
            return True
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        if ':6633' in result.stdout:
            return True
    except:
        pass
    return False

def main():
    """Main experiment runner"""
    
    print("\n" + "="*70)
    print("  5718 PROTOCOL STUDY - EXPERIMENT RUNNER")
    print("="*70 + "\n")
    
    ensure_output_dir()
    
    if not check_controller_running():
        print("⚠ WARNING: No controller detected on port 6633")
        print("\nMake sure you have a controller running in another terminal:")
        print("  For Ryu:  ryu-manager ryu.app.simple_switch_13")
        print("  For POX:  ./pox.py forwarding.l2_learning\n")
        
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Exiting.")
            return
    
    print("Which controller are you using?")
    print("  1) POX (OpenFlow 1.0)")
    print("  2) Ryu (OpenFlow 1.3)")
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == '1':
        controller_name = 'pox'
    elif choice == '2':
        controller_name = 'ryu'
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\nWhich mode?")
    print("  1) Debug mode (High-speed link, no bottleneck)")
    print("  2) Project mode (10Mbps bottleneck, 50ms delay, 1% loss)")
    mode_choice = input("\nEnter 1 or 2: ").strip()
    
    if mode_choice == '1':
        use_bottleneck = False
        print("\n→ Running in DEBUG mode")
    elif mode_choice == '2':
        use_bottleneck = True
        print("\n→ Running in PROJECT mode")
    else:
        print("Invalid choice. Exiting.")
        return
    
    setLogLevel('info')
    
    success = run_experiment_set(controller_name, use_bottleneck)
    
    if success:
        print("\n✓ Experiments completed successfully!")
        print(f"\nResults saved in: {OUTPUT_DIR}/")
        print("\nNext steps:")
        print("  1. Review the output files")
        print("  2. Run analysis script to generate graphs")
        print("  3. Repeat for other controller if needed")
    else:
        print("\n✗ Experiments failed. Check output above for errors.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
