#!/usr/bin/env python3
"""
Pre-Experiment Diagnostic Tool

Run this BEFORE running experiments to verify your setup is correct.
This will check:
1. Is Ryu controller running?
2. Can switches connect to controller?
3. Can basic connectivity work?
"""

import subprocess
import sys
import time
import os

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_check(text):
    print(f"\n[CHECK] {text}")

def run_command(cmd, capture=True):
    """Run command and return output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=5)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_ryu_process():
    """Check if Ryu controller is running"""
    print_check("Is Ryu controller running?")
    
    code, stdout, stderr = run_command("ps aux | grep ryu-manager | grep -v grep")
    
    if code == 0 and "ryu-manager" in stdout:
        print("  ✓ Ryu controller process found")
        print(f"  Process: {stdout.strip()[:80]}...")
        return True
    else:
        print("  ✗ Ryu controller NOT running!")
        print("  FIX: Start Ryu in another terminal:")
        print("       sudo ryu-manager ryu.app.simple_switch_13")
        return False

def check_controller_port():
    """Check if controller is listening on port 6633"""
    print_check("Is controller listening on port 6633?")
    
    # Try ss first
    code, stdout, stderr = run_command("sudo ss -tlnp | grep 6633")
    
    if code != 0:
        # Try netstat as fallback
        code, stdout, stderr = run_command("sudo netstat -tlnp | grep 6633")
    
    if code == 0 and "6633" in stdout:
        print("  ✓ Port 6633 is listening")
        print(f"  Details: {stdout.strip()[:80]}...")
        return True
    else:
        print("  ✗ Port 6633 NOT listening!")
        print("  FIX: Make sure Ryu is running")
        return False

def check_mininet_clean():
    """Check if Mininet is clean"""
    print_check("Is Mininet environment clean?")
    
    code, stdout, stderr = run_command("sudo ovs-vsctl list-br")
    
    if code == 0 and stdout.strip():
        print("  ⚠ Old Mininet bridges found:")
        for bridge in stdout.strip().split('\n'):
            print(f"    - {bridge}")
        print("  FIX: Run 'sudo mn -c' to clean up")
        return False
    else:
        print("  ✓ Mininet is clean (no old bridges)")
        return True

def test_basic_connectivity():
    """Test basic Mininet + Ryu connectivity"""
    print_check("Testing basic Mininet + Ryu connectivity...")
    
    print("  Creating simple 2-host network...")
    print("  (This will take ~15 seconds)")
    
    # Import here to avoid issues if Mininet not available
    try:
        from mininet.net import Mininet
        from mininet.node import RemoteController
        from mininet.topo import SingleSwitchTopo
        from mininet.log import setLogLevel
        
        setLogLevel('error')  # Quiet output
        
        # Create simple network
        topo = SingleSwitchTopo(2)
        net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633))
        
        net.start()
        time.sleep(5)  # Wait for convergence
        
        # Test ping
        h1 = net.get('h1')
        h2 = net.get('h2')
        
        result = h1.cmd('ping -c 3 -W 2 %s' % h2.IP())
        
        net.stop()
        
        # Check result
        if ' 0 received' in result or '100% packet loss' in result:
            print("  ✗ Ping test FAILED - no connectivity")
            print("  This means Ryu isn't properly controlling switches")
            return False
        else:
            print("  ✓ Ping test PASSED - connectivity works!")
            print("  Ryu is properly controlling switches")
            return True
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    
    print_header("PRE-EXPERIMENT DIAGNOSTIC TOOL")
    print("\nThis will verify your setup is ready for experiments.")
    print("Running checks...")
    
    # Run all checks
    checks = {
        "Ryu Process": check_ryu_process(),
        "Controller Port": check_controller_port(),
        "Mininet Clean": check_mininet_clean(),
    }
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check_name:20s} {status}")
        if not passed:
            all_passed = False
    
    # If basic checks pass, do connectivity test
    if checks["Ryu Process"] and checks["Controller Port"]:
        print("\n" + "-"*70)
        print("Basic checks passed. Running connectivity test...")
        print("-"*70)
        
        connectivity_ok = test_basic_connectivity()
        checks["Connectivity Test"] = connectivity_ok
        
        status = "✓ PASS" if connectivity_ok else "✗ FAIL"
        print(f"\n  {'Connectivity Test':20s} {status}")
        
        if not connectivity_ok:
            all_passed = False
    else:
        print("\n  ⚠ Skipping connectivity test (basic checks failed)")
        all_passed = False
    
    # Final verdict
    print("\n" + "="*70)
    if all_passed:
        print("  ✓✓✓ ALL CHECKS PASSED ✓✓✓")
        print("="*70)
        print("\nYour setup is ready!")
        print("\nNext step:")
        print("  $ sudo python3 run_clean_experiments.py")
        print("\nMake sure to keep the Ryu terminal open during experiments!")
        sys.exit(0)
    else:
        print("  ✗✗✗ SOME CHECKS FAILED ✗✗✗")
        print("="*70)
        print("\nYour setup is NOT ready.")
        print("\nFix the failed checks above, then run this diagnostic again.")
        print("\nMost common fix:")
        print("  1. Terminal 1: sudo ryu-manager ryu.app.simple_switch_13")
        print("  2. Terminal 2: sudo python3 pre_experiment_diagnostic.py")
        sys.exit(1)

if __name__ == '__main__':
    try:
        if os.geteuid() != 0:
            print("ERROR: This script must be run as root (use sudo)")
            sys.exit(1)
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
