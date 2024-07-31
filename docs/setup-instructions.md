## Setup Instructions

Please check our prerequisites [here](https://github.com/ARPA-Network/BLS-TSS-Network/blob/main/docs/eigenlayer-onboarding.md#prerequisites).

### Step 1: Clone the repo

```bash
git clone https://github.com/ARPA-Network/ARPA-Network-AVS-Monitoring.git
```

### Step 2: Update configuration

Fill `config-example.yml` file in the root directory, and rename it to `config.yml`

### Step 3: Start the tool

Ensure Docker is running and execute ('-d' will silent the terminal and run docker behind of screen):

```bash
docker compose up -d
```

You can use this to check the log of our monitoring tool as needed:

```bash
docker compose logs
```


### Step 4: Access Grafana

Go to loacalhost:3000 
Default login credentials are "admin:admin". These should be changed the first time you log in.
Wait for 30 seconds. You should be able to see data in Grafana (http://localhost:3000/d/dkg_dashboard/arpa-network-dashboard?orgId=1&refresh=30s). 

Example should look like ![dashboard example](./pictures/dashboard-example.png "dashboard example")

### Step 5 (Optional): Set up alert rules

1. Go to Alerting in Grafana.
2. Add your contact in the default location under Contacts.
3. You may also:
    - add custom alerting rules by following instructions from [Grafana documentation](https://grafana.com/docs/grafana/latest/alerting/).
    - change notification policy under "Alerting/Notification Policies" to choose contact, update resend policy, and etc. 


### Advanced Configurations

For users who are interested in advanced configuration , please see [here](./advanced-config-operations.md)