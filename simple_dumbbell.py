#!/usr/bin/env python
"""
Simple Dumbbell Topology for 5718 Project
- 22 nodes total (16 hosts, 6 switches)
- Works with both POX and Ryu controllers
- Configurable bottleneck link
"""

from mininet.topo import Topo

class SimpleDumbbellTopo(Topo):
    """
    Dumbbell topology:
    
    Left Side:                    Right Side:
    h1 ─┐                              ┌─ h9
    h2 ─┤                              ├─ h10
    h3 ─┼─ s1 ─┐                  ┌─ s4 ─┼─ h11
    h4 ─┘       │                  │       └─ h12
                ├─ r1 ──[bottleneck]── r2 ─┤
    h5 ─┐       │                  │       ┌─ h13
    h6 ─┤       │                  │       ├─ h14
    h7 ─┼─ s2 ─┘                  └─ s5 ─┼─ h15
    h8 ─┘                              └─ h16
                                       
                                       ┌─ h17
                                       ├─ h18
                                   s3 ─┼─ h19
                                       └─ h20
                                       
                                       ┌─ h21
                                   s6 ─┴─ h22
    
    Total: 22 hosts, 6 switches (s1-s6), 2 core routers (r1, r2)
    """
    
    def build(self, bottleneck_bw=10, bottleneck_delay='50ms', 
              bottleneck_loss=1, use_bottleneck=False):
        """
        Args:
            bottleneck_bw: Bottleneck bandwidth in Mbps (default: 10)
            bottleneck_delay: Bottleneck delay (default: '50ms')
            bottleneck_loss: Bottleneck packet loss % (default: 1)
            use_bottleneck: If False, use high-speed link for testing (default: False)
        """
        
        r1 = self.addSwitch('r1')
        r2 = self.addSwitch('r2')
        
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        
        self.addLink(s1, r1, bw=1000)
        self.addLink(s2, r1, bw=1000)
        self.addLink(s3, r1, bw=1000)
        self.addLink(s4, r2, bw=1000)
        self.addLink(s5, r2, bw=1000)
        self.addLink(s6, r2, bw=1000)
        
        if use_bottleneck:
            self.addLink(r1, r2, bw=bottleneck_bw, delay=bottleneck_delay, 
                        loss=bottleneck_loss, max_queue_size=100)
            print(f"*** Using BOTTLENECK: {bottleneck_bw}Mbps, "
                  f"{bottleneck_delay} delay, {bottleneck_loss}% loss")
        else:
            self.addLink(r1, r2, bw=1000)
            print("*** Using DEBUG MODE: 1Gbps link (no constraints)")
        
        # Create hosts and connect to switches
        # Left side - s1 (h1-h4)
        for i in range(1, 5):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(h, s1)
        
        # Left side - s2 (h5-h8)
        for i in range(5, 9):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(h, s2)
        
        # Left side - s3 (h9-h12) - Wait, let's keep it simple
        
        # Right side - s4 (h9-h12)
        for i in range(9, 13):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(h, s4)
        
        # Right side - s5 (h13-h16)
        for i in range(13, 17):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(h, s5)
        
        # Right side - s6 (h17-h20)
        for i in range(17, 21):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(h, s6)
        
        # Additional hosts for s3 (h21-h22) to reach 22 total
        for i in range(21, 23):
            h = self.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
            self.addLink(h, s3)

# Topos available for 'mn --custom' command
topos = {
    'simple_dumbbell': SimpleDumbbellTopo,
    'debug': lambda: SimpleDumbbellTopo(use_bottleneck=False),
    'project': lambda: SimpleDumbbellTopo(use_bottleneck=True)
}
