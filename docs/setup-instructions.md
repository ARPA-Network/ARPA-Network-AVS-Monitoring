## Setup Instructions

### Prerequisites:

- Linux Ubuntu (22.04 and above)
- RAM: 4 GB 
- CPU: 2 cores
- Docker and git installed

### Step 1: Clone the repo

```bash
git clone https://github.com/ARPA-Network/ARPA-Network-AVS-Monitoring.git
```

### Step 2: Update configuration

Update `config.yml` file in the root directory.

### Step 3: Run setup script

```bash
chmod +x setup.sh
./setup.sh
```

### Step 3.5 [Temporary step - to be deleted later]:

1. Rename `docker-compose-example.yml` to `docker-compose.yml` and update AWS secret manually.
2. Manually build the custom exporter image:

```bash
cd custom-exporter
docker build -t custom-exporter:latest .
cd ..
```

### Step 4: Start the tool

Ensure Docker is running and execute:

```bash
docker compose up -d
```

### Step 5: Access Grafana

Wait for 30 seconds. You should be able to see data in Grafana (http://localhost:3000). 
First-time login credentials are in the `docker-compose.yml` file.

### Step 6 (Optional): Set up alert rules

1. Go to Alerting in Grafana.
2. Add your contact in the default location under Contacts.
3. You may also add custom alerting rules by following instructions from [Grafana documentation](https://grafana.com/docs/grafana/latest/alerting/).