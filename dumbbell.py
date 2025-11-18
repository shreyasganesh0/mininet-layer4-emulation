from mininet.topo import Topo
from mininet.link import TCLink

class DumbbellTopo(Topo):
    "Dumbbell topology for 5718 Project: 22 Nodes total"

    def build(self):
        rA = self.addSwitch('r1')
        rB = self.addSwitch('r2')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        self.addLink(s1, rA, bw=1000)
        self.addLink(s2, rA, bw=1000)
        self.addLink(s3, rB, bw=1000)
        self.addLink(s4, rB, bw=1000)

        self.addLink(rA, rB, bw=10, delay='50ms', loss=1, max_queue_size=100)

        # Total Nodes: 16 hosts + 6 switches = 22 nodes
        for i in range(1, 5):
            h = self.addHost(f'h1_{i}')
            self.addLink(h, s1)
        
        for i in range(1, 5):
            h = self.addHost(f'h2_{i}')
            self.addLink(h, s2)

        for i in range(1, 5):
            h = self.addHost(f'h3_{i}')
            self.addLink(h, s3)

        for i in range(1, 5):
            h = self.addHost(f'h4_{i}')
            self.addLink(h, s4)

topos = { 'dumbbell': ( lambda: DumbbellTopo() )}
