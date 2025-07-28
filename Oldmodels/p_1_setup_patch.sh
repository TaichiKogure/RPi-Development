#!/bin/bash
# p1_setup.sh: Raspberry Pi 5 setup script with venv and new data directory

set -e

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies including venv
sudo apt install -y python3-venv git

# 3. Set up virtual environment
cd ~
python3 -m venv envmonitor-venv
source envmonitor-venv/bin/activate

# 4. Install required Python packages
pip install flask flask-socketio pandas plotly

# 5. Create data directory outside raspap scope
sudo mkdir -p /var/lib(FromThonny)/envmonitor/data
sudo chown -R $USER:$USER /var/lib(FromThonny)/envmonitor/data

# 6. Clone project or copy files manually (adjust as needed)
# git clone https://github.com/example/RaspPi5_APconnection.git

# 7. Create sample systemd service with updated paths and user
SERVICE_FILE=/etc/systemd/system/data_collector.service
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Environmental Data Collector
After=network.target

[Service]
ExecStart=/home/$USER/envmonitor-venv/bin/python3 /home/$USER/RaspPi5_APconnection/p1_software/data_collection/data_collector.py
WorkingDirectory=/home/$USER/RaspPi5_APconnection/p1_software/data_collection
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOF

# 8. Enable and start the service
sudo systemctl daemon-reexec
sudo systemctl enable data_collector.service
sudo systemctl start data_collector.service

# 9. Done
echo "Setup complete. Data will be saved to /var/lib/envmonitor/data."
echo "Flask and related packages installed in Python virtual environment: ~/envmonitor-venv"
echo "Use 'source ~/envmonitor-venv/bin/activate' to activate it."
