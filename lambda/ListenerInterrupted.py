import boto3
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    node_id = event['queryStringParameters']['node_id']
    
    cloudwatch = boto3.client('cloudwatch')
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)  
    
    metrics = cloudwatch.list_metrics(
        Namespace='arpa-network-logs-test',
        MetricName='ListenerInterrupted',
        Dimensions=[{'Name': 'node_id', 'Value': node_id}]
    )

    all_data = []

    for metric in metrics['Metrics']:
        dimensions = metric['Dimensions']
        
        response = cloudwatch.get_metric_statistics(
            Namespace='arpa-network-logs-test',
            MetricName='ListenerInterrupted',
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=60,  
            Statistics=['Sum']
        )
        
        datapoints = response['Datapoints']
        formatted_data = [
            {
                'timestamp': d['Timestamp'].isoformat(),
                'sum': d['Sum'],
                'dimensions': {dim['Name']: dim['Value'] for dim in dimensions}
            } for d in datapoints
        ]
        
        all_data.extend(formatted_data)

    return {
        'statusCode': 200,
        'body': json.dumps(all_data)
    }