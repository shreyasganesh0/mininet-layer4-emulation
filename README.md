# Mininet Layer4 Protocols Emulation Testing

## Prerequistites

1. Python3
```
sudo apt install python3
```

2. Metrics Dependencies
```
sudo apt-get update
sudo apt-get install iperf3 python3-matplotlib
```

3. Ryu Controller
```
sudo pip3 install ryu
sudo pip3 install eventlet==0.30.2
```

4. Pox Controller
```
git clone https://github.com/noxrepo/pox
cd pox
python3 pox.py forwarding.l2_learning
cp dns.py pox/pox/lib/packet 
```

## Usage

- Optional Verification
```
chmod +x verify_setup.sh

./verify_setup.sh
```
- use to verify all dependencies exist before
running the experiments

1. Pox controller

- open terminal 1
```
cd pox

./pox.py forwarding.12_learning
```

- open another terminal
```
sudo python3 run_clean_experiments.py
    - choose experiment 1 for POX
```

2. Ryu controller

- open terminal 1
```
ryu-manager ryu.app.simple_switch_13
```

- open another terminal
```
sudo python3 run_clean_experiments.py
    - choose experiment 2 for RYU 
```

3. Analysis

- generate plots
```
python3 analyze_results.py
```
