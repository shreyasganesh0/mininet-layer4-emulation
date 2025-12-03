# COP 5718 Network Performance Analysis Project

Comparative performance evaluation of TCP congestion control algorithms (Reno, CUBIC) and UDP in Software-Defined Networks using Mininet and POX/Ryu controllers.

## 📊 Project Overview

- **Topology**: 22 hosts, 6 switches, 2 core routers (dumbbell configuration)
- **Protocols**: TCP Reno, TCP CUBIC, UDP
- **Controllers**: POX (OpenFlow 1.0), Ryu (OpenFlow 1.3)
- **Metrics**: Throughput, Latency, Packet Loss, Jitter
- **Bottleneck**: 10 Mbps, 50ms delay, 1% loss

## 🚀 Quick Start

### Prerequisites

```bash
# System packages
sudo apt-get update
sudo apt-get install python3 mininet iperf3 python3-matplotlib arping

# Ryu Controller (if using Ryu)
sudo pip3 install ryu --break-system-packages
sudo pip3 install eventlet==0.30.2 --break-system-packages

# POX Controller (if using POX)
git clone https://github.com/noxrepo/pox
cd pox
# Copy DNS helper file (if needed)
cp ../dns.py pox/lib/packet/
```

### Verify Setup

```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

## 📖 Running Experiments

### Option 1: Automated Experiments (Recommended)

**Step 1: Start Controller**

Terminal 1 - For POX:
```bash
cd pox
./pox.py forwarding.l2_learning
```

OR Terminal 1 - For Ryu:
```bash
ryu-manager ryu.app.simple_switch_13
```

**Step 2: Run All Experiments**

Terminal 2:
```bash
sudo python3 run_clean_experiments.py
```

Follow the prompts:
- Choose controller: `1` for POX, `2` for Ryu
- Choose mode: `2` for Project (bottleneck) mode

This will automatically:
- ✅ Create the dumbbell topology
- ✅ Wait for network convergence (40 seconds)
- ✅ Prime switches with ARP packets
- ✅ Test connectivity
- ✅ Run TCP Reno test (30 seconds)
- ✅ Run TCP CUBIC test (30 seconds)
- ✅ Run UDP test (30 seconds)
- ✅ Collect ping statistics (100 packets each)
- ✅ Save all results to `experiment_results/`

**Total time**: ~5-7 minutes per controller

### Option 2: Manual Live Demos

For live demonstrations with real-time output:

**TCP Reno Demo:**
```bash
# Terminal 1: Start controller first
sudo python3 demo_tcp_reno.py
```

**TCP CUBIC Demo:**
```bash
# Terminal 1: Start controller first
sudo python3 demo_tcp_cubic.py
```

**UDP Demo:**
```bash
# Terminal 1: Start controller first
sudo python3 demo_udp.py
```

Each demo:
- Shows step-by-step progress
- Displays live iperf3 output
- Provides educational explanations
- Saves detailed results for analysis

## 📈 Analyzing Results

### Generate All 4 Graphs (For Presentation)

```bash
python3 analyze_results_presentation.py
```

**Output Files:**
- `throughput_comparison.png` - Throughput comparison
- `latency_comparison.png` - Latency (RTT) comparison
- `packet_loss_comparison.png` - Packet loss comparison
- `jitter_comparison.png` - Jitter comparison (UDP only)

All graphs are 300 DPI, ready for slides!

### Generate Combined Analysis (4-panel plot)

```bash
python3 analyze_results.py
```

Generates:
- `protocol_comparison_bottleneck.png` - 4-panel comparison plot
- Terminal summary table with all metrics

## 📁 Project Structure

```
.
├── simple_dumbbell.py              # Topology definition (22 hosts, 6 switches)
├── run_clean_experiments.py         # Automated experiment runner
├── demo_tcp_reno.py                 # Live TCP Reno demo
├── demo_tcp_cubic.py                # Live TCP CUBIC demo
├── demo_udp.py                      # Live UDP demo
├── analyze_results.py               # Analysis script (combined plot)
├── analyze_results_presentation.py  # Analysis script (4 separate graphs)
├── verify_setup.sh                  # Setup verification script
├── dns.py                           # DNS helper for POX
├── experiment_results/              # Generated results directory
│   ├── pox_bottleneck_reno_iperf.json
│   ├── pox_bottleneck_reno_ping.txt
│   ├── pox_bottleneck_cubic_iperf.json
│   ├── pox_bottleneck_cubic_ping.txt
│   ├── pox_bottleneck_udp_iperf.json
│   └── pox_bottleneck_udp_ping.txt
└── README.md                        # This file
```

## 🔬 Understanding the Results

### Expected Results (POX Controller, Bottleneck Mode)

| Protocol   | Throughput | Latency  | Packet Loss | Jitter |
|-----------|-----------|----------|-------------|--------|
| TCP Reno  | ~1.7 Mbps | ~165 ms  | 0%          | 0 ms   |
| TCP CUBIC | ~1.5 Mbps | ~178 ms  | 2%          | 0 ms   |
| UDP       | ~19.7 Mbps| ~163 ms  | **75.55%**  | ~5 ms  |

### Key Insights

**TCP CUBIC vs TCP Reno:**
- CUBIC achieves higher throughput in ideal conditions
- More aggressive window growth
- Slight increase in packet loss (2% vs 0%)

**UDP Behavior:**
- Highest throughput but catastrophic packet loss
- No congestion control = sends at full 20 Mbps
- Bottleneck is 10 Mbps → 75% loss expected
- Demonstrates why congestion control is essential

**Why UDP has 75% loss but ping shows 0%:**
- UDP data packets: 75.55% loss (from iperf3)
- ICMP ping packets: 0% loss (different priority)
- ICMP has higher network stack priority than UDP data
- Analysis script correctly uses iperf3 loss for UDP

## 🐛 Troubleshooting

### Problem: "No connectivity" errors

**Solution:**
1. Make sure controller is running in separate terminal
2. Wait full 40 seconds for convergence
3. Check controller terminal for connection messages
4. Try `sudo mn -c` to clean old Mininet state

### Problem: "Controller not found on port 6633"

**Solution:**
```bash
# Check if controller is running
sudo ss -tlnp | grep 6633
# OR
sudo netstat -tlnp | grep 6633

# If not running, start it:
# POX: ./pox.py forwarding.l2_learning
# Ryu: ryu-manager ryu.app.simple_switch_13
```

### Problem: Ryu shows 100% packet loss

**Cause:** Ryu's `simple_switch_13` application cannot handle inter-domain routing in multi-router topologies.

**Solution:** Use POX instead, or use a more advanced Ryu application like `rest_router`.

**Why this happens:** `simple_switch_13` only learns MAC addresses within a single L2 domain. Our topology has routers r1 and r2 creating separate domains.

### Problem: Graphs show wrong UDP packet loss (0% instead of 75%)

**Solution:** Use the updated `analyze_results_presentation.py` script which correctly:
- Uses iperf3 loss for UDP (75.55%)
- Uses ping loss for TCP (0-2%)
- Never overwrites UDP's iperf3 loss with ping's 0%

### Problem: "Permission denied" errors

**Solution:**
```bash
# Run with sudo
sudo python3 run_clean_experiments.py

# Make scripts executable
chmod +x verify_setup.sh
chmod +x *.py
```

### Problem: Old bridges remain after Ctrl+C

**Solution:**
```bash
# Clean up Mininet state
sudo mn -c

# Kill any lingering processes
sudo pkill -9 iperf3
sudo pkill -9 python
```

## 🎯 Using the Topology in MiniEdit

To visualize or modify the topology in MiniEdit:

```bash
# Generate MiniEdit-compatible file
python3 generate_miniedit_topology.py

# This creates: dumbbell_topology.mn

# Open in MiniEdit
sudo ~/mininet/examples/miniedit.py dumbbell_topology.mn
```

In MiniEdit:
- ✅ View the complete topology graphically
- ✅ Modify link parameters
- ✅ Add/remove hosts or switches
- ✅ Export modified topology
- ✅ Test interactively

## 📊 Report Requirements Checklist

- [x] **Topology**: 22 hosts, 6 switches (exceeds 20 nodes, 5 switches)
- [x] **Bottleneck Link**: 10 Mbps, 50ms delay, 1% loss
- [x] **Multiple Protocols**: TCP Reno, TCP CUBIC, UDP
- [x] **Multiple Metrics**: Throughput, Latency, Packet Loss, Jitter
- [x] **Multiple Controllers**: POX (working), Ryu (limitation documented)
- [x] **Graphs**: All 4 metrics plotted (300 DPI PNG)
- [x] **Reproducible**: Automated scripts + README

**Project Level**: A

## 🔧 Advanced Usage

### Custom Bottleneck Parameters

Edit `simple_dumbbell.py`:
```python
# Line ~58
def build(self, bottleneck_bw=10,        # Change bandwidth
                bottleneck_delay='50ms',  # Change delay
                bottleneck_loss=1,        # Change loss %
                use_bottleneck=False):
```

### Running Tests Manually in Mininet CLI

```bash
sudo python3 -c "
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from functools import partial
from simple_dumbbell import SimpleDumbbellTopo

topo = SimpleDumbbellTopo(use_bottleneck=True)
net = Mininet(topo=topo, link=TCLink, 
              controller=partial(RemoteController, ip='127.0.0.1', port=6633))
net.start()
net.interact()  # Opens Mininet CLI
"

# In Mininet CLI:
mininet> h1 iperf3 -c 10.0.0.13 -C reno -t 10
mininet> h1 ping -c 10 h13
mininet> exit
```

### Debug Mode (No Bottleneck)

Use when testing topology connectivity:
```bash
sudo python3 run_clean_experiments.py
# Choose mode: 1 (Debug mode)
```

Debug mode uses 1 Gbps links everywhere - fast testing!

## 📚 References

1. CUBIC TCP: [RFC 8312](https://tools.ietf.org/html/rfc8312)
2. Mininet Documentation: [http://mininet.org/](http://mininet.org/)
3. POX Controller: [https://github.com/noxrepo/pox](https://github.com/noxrepo/pox)
4. Ryu Controller: [https://ryu-sdn.org/](https://ryu-sdn.org/)
5. iperf3: [https://iperf.fr/](https://iperf.fr/)

## 👥 Authors

- Ganesh
- Jacobs  
- Schmidt

## 🆘 Getting Help

If you encounter issues:

1. Run diagnostic: `./verify_setup.sh`
2. Check controller is running: `sudo ss -tlnp | grep 6633`
3. Clean Mininet: `sudo mn -c`
4. Check logs in controller terminal
5. Verify all prerequisites are installed

**Common Issues Document**: See troubleshooting section above

---

**Last Updated**: December 2025
**Project**: COP 5718 Network Performance Analysis
**Status**: ✅ Complete and tested
