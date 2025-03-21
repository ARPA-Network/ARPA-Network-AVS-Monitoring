# Change Config of Each Component

Our config setup script will automatically set most of the configs you need. However, if you wish to modify certain attributes by your own, here are their locations:

## Grafana
- Basic settings are in `docker-compose.yaml` file
- Other settings can be found in front-end webpage (localhost:3000 by default)

## Custom Exporter
- You may need to update `docker-compose.yaml` and `config.yml`

## Prometheus
- Basic settings are in `docker-compose.yaml` file
- `prometheus.yml` for the connectivity with custom exporter

## Examples

### Change Scrape Interval
- **Grafana**: change in the webpage (auto-refresh time)
- **Prometheus**: scrape_interval in 'prometheus.yml'
- **Custom Exporter**: interval section in "config.yml"

### Change Ports

We recommend to only update ports in docker-compose.yml like '[your custom ports]:9090' so that the general connectivity remains the same. 