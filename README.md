# ARPA-Network-AVS-Monitoring
## Overview

This repo contains a dashboard solution that allows you to monitor that status of your [ARPA Network AVS Operator Node](https://github.com/arPA-Network/BLS-TSS-Network/).

To set it up, please refer to the [setup instructions](docs/setup-instructions.md).

## Components

**Scrape interval**: 30 seconds

### Custom Exporter
- **Functionality**: Pull on-chain data
- **Default URL**: `localhost:8000`

### Prometheus
- **Functionality**: Metrics collection
- **Default URL**: `localhost:9090`

### Grafana
- **Functionality**: Visualization and alerting
- **Default URL**: `localhost:3000`

## Workflow

1. **Data Collection**: 
   Custom Exporter is responsible for data collection as it:
   - pulls on-chain data
   - and extracts information from stored logs

2. **Data Processing**: 
   - Prometheus transforms the collected data into metrics (gauges)

3. **Visualization and Alerting**: 
   - Grafana receives the metrics from Prometheus
   - Displays them on dashboards
   - Triggers alerts based on predefined rules

## Metrics Avaliable

You may access metrics from different components. For example, you can retreive data from Prometheus programmatically or Grafana visually. You can also grab data from Custom Exporter directly as needed. 

- Node State: if the node is activated 
- Node Address: the node account address you are monitoring 
- ETH Balance: current eth balance of the node account monitored 
- Group Index: index of the group this node belongs to 
- Group State: if the group is functioning 
- Group Size: count of group members 
- DKG Grouping State: if DKG process is finished, still processing or overrun 
- Committer Addresses: committer nodes of the current group 

Note: Below metrics may not always have data since current traffic is low.

- Partial Signature Generation Processing Time: average processing time of requests per minute 
- Randomness Task Count: Task received per minute 
- Reconnection Attempts Count: count of listener interrupted error per minute 

## Default Alert Rules

We currently have 3 rules set by default:

1. If node is deactivated
2. If node account balance is less than 0.1 ETH
3. If there are more than 10 RPC reconnection attempts within a minute

To use these rules, you can follow [setup instructions step #6](docs/setup-instructions.md#step-6-optional-set-up-alert-rules).
