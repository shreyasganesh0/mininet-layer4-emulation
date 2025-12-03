#!/usr/bin/env python3
"""
Generate MiniEdit-Compatible Topology File
Creates a .mn file that can be opened in MiniEdit GUI

Usage:
    python3 generate_miniedit_topology.py
    
Then open in MiniEdit:
    sudo ~/mininet/examples/miniedit.py dumbbell_topology.mn
"""

import json

def generate_miniedit_topology():
    """
    Generate MiniEdit-compatible JSON topology
    Represents the 22-host, 6-switch, 2-router dumbbell topology
    """
    
    topology = {
        "application": {
            "dpctl": "",
            "ipBase": "10.0.0.0/8",
            "netflow": {
                "nflowAddId": "0",
                "nflowTarget": "",
                "nflowTimeout": "600"
            },
            "openFlowVersions": {
                "ovsOf10": "1",
                "ovsOf11": "0",
                "ovsOf12": "0",
                "ovsOf13": "0"
            },
            "sflow": {
                "sflowHeader": "128",
                "sflowPolling": "30",
                "sflowSampling": "400",
                "sflowTarget": ""
            },
            "startCLI": "1",
            "switchType": "ovs",
            "terminalType": "xterm"
        },
        "controllers": [
            {
                "opts": {
                    "controllerProtocol": "tcp",
                    "controllerType": "remote",
                    "hostname": "c0",
                    "remoteIP": "127.0.0.1",
                    "remotePort": 6633
                },
                "x": "400",
                "y": "100"
            }
        ],
        "hosts": [],
        "links": [],
        "switches": [],
        "version": "2"
    }
    
    # Define switch positions for nice visualization
    switch_positions = {
        's1': (200, 250),
        's2': (200, 350),
        's3': (200, 450),
        'r1': (350, 350),  # Core router 1
        'r2': (650, 350),  # Core router 2
        's4': (800, 250),
        's5': (800, 350),
        's6': (800, 450)
    }
    
    # Create switches
    for switch_name, (x, y) in switch_positions.items():
        switch = {
            "number": switch_name.replace('s', '').replace('r', ''),
            "opts": {
                "controllers": ["c0"],
                "hostname": switch_name,
                "nodeNum": int(switch_name.replace('s', '').replace('r', '')),
                "switchType": "ovs"
            },
            "x": str(x),
            "y": str(y)
        }
        topology['switches'].append(switch)
    
    # Define host positions
    # Left side hosts
    left_hosts = {
        # s1 hosts (h1-h4)
        'h1': (100, 200),
        'h2': (100, 230),
        'h3': (100, 260),
        'h4': (100, 290),
        # s2 hosts (h5-h8)
        'h5': (100, 320),
        'h6': (100, 350),
        'h7': (100, 380),
        'h8': (100, 410),
        # s3 hosts (h21-h22)
        'h21': (100, 440),
        'h22': (100, 470),
    }
    
    # Right side hosts
    right_hosts = {
        # s4 hosts (h9-h12)
        'h9': (900, 200),
        'h10': (900, 230),
        'h11': (900, 260),
        'h12': (900, 290),
        # s5 hosts (h13-h16)
        'h13': (900, 320),
        'h14': (900, 350),
        'h15': (900, 380),
        'h16': (900, 410),
        # s6 hosts (h17-h20)
        'h17': (900, 440),
        'h18': (900, 470),
        'h19': (900, 500),
        'h20': (900, 530),
    }
    
    all_hosts = {**left_hosts, **right_hosts}
    
    # Create hosts
    for host_name, (x, y) in all_hosts.items():
        host_num = int(host_name.replace('h', ''))
        host = {
            "number": str(host_num),
            "opts": {
                "hostname": host_name,
                "nodeNum": host_num,
                "sched": "host"
            },
            "x": str(x),
            "y": str(y)
        }
        topology['hosts'].append(host)
    
    # Create links
    links = []
    
    # Left side switch-to-router links (1Gbps)
    links.append({"src": "s1", "dest": "r1", "bw": 1000})
    links.append({"src": "s2", "dest": "r1", "bw": 1000})
    links.append({"src": "s3", "dest": "r1", "bw": 1000})
    
    # Right side switch-to-router links (1Gbps)
    links.append({"src": "s4", "dest": "r2", "bw": 1000})
    links.append({"src": "s5", "dest": "r2", "bw": 1000})
    links.append({"src": "s6", "dest": "r2", "bw": 1000})
    
    # BOTTLENECK LINK (r1 <-> r2)
    links.append({
        "src": "r1", 
        "dest": "r2", 
        "bw": 10,           # 10 Mbps
        "delay": "50ms",    # 50ms delay
        "loss": 1,          # 1% loss
        "max_queue_size": 100
    })
    
    # Host-to-switch links
    # s1 hosts
    for i in range(1, 5):
        links.append({"src": f"h{i}", "dest": "s1"})
    
    # s2 hosts
    for i in range(5, 9):
        links.append({"src": f"h{i}", "dest": "s2"})
    
    # s3 hosts
    links.append({"src": "h21", "dest": "s3"})
    links.append({"src": "h22", "dest": "s3"})
    
    # s4 hosts
    for i in range(9, 13):
        links.append({"src": f"h{i}", "dest": "s4"})
    
    # s5 hosts
    for i in range(13, 17):
        links.append({"src": f"h{i}", "dest": "s5"})
    
    # s6 hosts
    for i in range(17, 21):
        links.append({"src": f"h{i}", "dest": "s6"})
    
    # Convert links to MiniEdit format
    for link in links:
        src = link['src']
        dest = link['dest']
        
        link_obj = {
            "dest": dest,
            "opts": {},
            "src": src
        }
        
        # Add bandwidth if specified
        if 'bw' in link:
            link_obj['opts']['bw'] = link['bw']
        
        # Add delay if specified
        if 'delay' in link:
            link_obj['opts']['delay'] = link['delay']
        
        # Add loss if specified
        if 'loss' in link:
            link_obj['opts']['loss'] = link['loss']
        
        # Add max_queue_size if specified
        if 'max_queue_size' in link:
            link_obj['opts']['max_queue_size'] = link['max_queue_size']
        
        topology['links'].append(link_obj)
    
    return topology

def save_topology(topology, filename='dumbbell_topology.mn'):
    """Save topology to MiniEdit format"""
    with open(filename, 'w') as f:
        json.dump(topology, f, indent=2)
    print(f"✓ MiniEdit topology saved to: {filename}")
    print(f"\nTo open in MiniEdit:")
    print(f"  sudo ~/mininet/examples/miniedit.py {filename}")
    print(f"\nOr if MiniEdit is in a different location:")
    print(f"  sudo python3 /path/to/miniedit.py {filename}")

def main():
    """Generate and save MiniEdit topology"""
    print("\n" + "="*70)
    print("  MINIEDIT TOPOLOGY GENERATOR")
    print("  Dumbbell Topology: 22 hosts, 6 switches, 2 routers")
    print("="*70 + "\n")
    
    print("Generating topology...")
    topology = generate_miniedit_topology()
    
    print(f"  ✓ {len(topology['hosts'])} hosts")
    print(f"  ✓ {len(topology['switches'])} switches")
    print(f"  ✓ {len(topology['links'])} links")
    print(f"  ✓ {len(topology['controllers'])} controller\n")
    
    save_topology(topology)
    
    print("\nTopology Details:")
    print("  • Left side: h1-h8, h21-h22 (10 hosts)")
    print("  • Right side: h9-h20 (12 hosts)")
    print("  • Switches: s1, s2, s3 (left), s4, s5, s6 (right)")
    print("  • Core routers: r1 (left), r2 (right)")
    print("  • Bottleneck: r1 ↔ r2 (10 Mbps, 50ms delay, 1% loss)")
    print("\nTest path:")
    print("  h1 (10.0.0.1) → s1 → r1 → [BOTTLENECK] → r2 → s5 → h13 (10.0.0.13)")
    print("\n" + "="*70)
    print("  READY TO OPEN IN MINIEDIT!")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
