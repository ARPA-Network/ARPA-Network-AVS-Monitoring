# ARPA-Network-AVS-Monitoring
## Overview

To set it up, please refer to the [setup instructions here](docs/setup-instructions.md).

## Components

### Custom Exporter
- **Functionality**: Pull on-chain data
- **Scrape interval**: 10 seconds
- **Default URL**: `localhost:8000`

### AWS Exporter
- **Functionality**: Pull log info analysis
- **Scrape interval**: 25 seconds
- **Default URL**: `localhost:9106`

### Prometheus
- **Functionality**: Metrics collection
- **Scrape interval**: 25 seconds
- **Default URL**: `localhost:9090`

### Grafana
- **Functionality**: Visualization and alerting
- **Scrape interval**: 30 seconds
- **Default URL**: `localhost:3000`

## Workflow

1. **Data Collection**: 
   - Custom Exporter pulls on-chain data
   - AWS Exporter extracts information from stored logs

2. **Data Processing**: 
   - Prometheus transforms the collected data into metrics (gauges)

3. **Visualization and Alerting**: 
   - Grafana receives the metrics from Prometheus
   - Displays them on dashboards
   - Triggers alerts based on predefined rules

## Default Alert Rules

We currently have 3 rules set by default:

1. If node is activated
2. If node account balance is over 0.1 ETH
3. If there are more than 10 RPC reconnection attempts within a minute

To use these rules, you can follow [setup instructions step #6](docs/setup-instructions.md).