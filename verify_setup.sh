#!/bin/bash
# Quick Start Verification Script
# Tests that everything is set up correctly

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  5718 PROJECT - SETUP VERIFICATION${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python3
echo -n "Checking Python3... "
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Install: sudo apt-get install python3"
fi

# Check Mininet
echo -n "Checking Mininet... "
if command -v mn &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Install: sudo apt-get install mininet"
fi

# Check iperf3
echo -n "Checking iperf3... "
if command -v iperf3 &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Install: sudo apt-get install iperf3"
fi

# Check Ryu
echo -n "Checking Ryu... "
if python3 -c "import ryu" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Install: pip3 install ryu --break-system-packages"
fi

# Check matplotlib
echo -n "Checking matplotlib... "
if python3 -c "import matplotlib" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Not found (optional, needed for plots)${NC}"
    echo "  Install: pip3 install matplotlib"
fi

# Check files
echo ""
echo "Checking project files:"

for file in "simple_dumbbell.py" "run_clean_experiments.py" "analyze_results.py"; do
    echo -n "  $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  QUICK TEST${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "This will test the topology file..."
echo ""

# Test topology import
python3 << 'EOF'
try:
    from simple_dumbbell import SimpleDumbbellTopo
    topo = SimpleDumbbellTopo(use_bottleneck=False)
    print("✓ Topology file is valid")
except Exception as e:
    print(f"✗ Topology file has errors: {e}")
EOF

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  NEXT STEPS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "To run experiments:"
echo ""
echo "1. Start a controller:"
echo "   ${YELLOW}For Ryu:${NC}  ryu-manager ryu.app.simple_switch_13"
echo "   ${YELLOW}For POX:${NC}  ./pox.py forwarding.l2_learning"
echo ""
echo "2. Run experiments (in another terminal):"
echo "   ${YELLOW}sudo python3 run_clean_experiments.py${NC}"
echo ""
echo "3. Analyze results:"
echo "   ${YELLOW}python3 analyze_results.py${NC}"
echo ""
echo -e "${GREEN}Good luck with your project!${NC}"
echo ""
