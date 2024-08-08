## Reward Policy

Our rewards are distributed every 30 days, and to get rewards, you will need to fulfill the following requirements during each period (for more details, please reach out to our Telegram group):


1. Restaked amount is above 100 ETH
2. Have sufficient balance on required L1/L2 chains (L1 to have 0.2 ETH and L2 chains to have 0.05 ETH)
3. Use a stable WSS connection provider and make sure there is no deactivation
4. Node client is able to respond to and fulfill randomness tasks at least once

## Additional Tips and Warnings
1. We have provided alerts in our monitoring tool to notify you of insufficient balance and unstable connections 
    - to use the alert, please follow [setup instructions step #5](docs/setup-instructions.md#step-5-optional-set-up-alert-rules).
    - to check history state of alert, you can go to alerting/alert rules, expand the rule you want to see then click `Show state history`, like ![state history example](./pictures/alert-state.png "state history example")

2. To see if you have completed any randomness tasks within the last 30 days, you will need to change the range in Grafana to "Last 30 days" (you can find this setting in the top right section of the dashboard page)
3. To ensure no metric data is missed, we highly suggest you keep this monitoring tool always on and do not remove your Docker container instance.
