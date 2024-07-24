# Change Config of Each Component

Our config setup script will automatically set most of the configs you need. However, if you wish to modify certain attributes by your own, here are their locations:

## Grafana
- Basic settings are in `docker-compose.yaml` file
- Other settings can be found in front-end webpage (localhost:3000 by default)

## AWS Exporter
- Basic settings are in `docker-compose.yaml` file 'cloudwatch-exporter' section
- Metric settings are in the 'aws_exporter_config.yml' file

## Custom Exporter
- You may need to update `docker-compose.yaml` and 'custom-exporter/exporter-config.yml' 

## Prometheus
- Basic settings are in `docker-compose.yaml` file
- 'prometheus.yml' for the connectivities with other exporters

## Examples

### Change Scrape Interval
- **Grafana**: change in the webpage (auto-refresh time)
- **Prometheus**: scrape_interval in 'prometheus.yml'
- **AWS Exporter**: it should be same as prometheus, but if you want additional delays, you can add "delay_seconds" in aws_exporter_config.yml
- **Custom Exporter**: interval section in "exporter-config.yml"

### Change Ports

We recommend to only update ports in docker-compose.yml like '<your custom ports>:9090' so that the general connectivities remains the same. 