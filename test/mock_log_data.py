import boto3
import time
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

region = 'us-east-1'

logs_client = boto3.client('logs', region_name=region)
log_group_name = 'arpa-network-logs'
log_stream_name = '0x1234567890123456789012345678901234567890'
LISTENER_INTERRUPTED = '{"time":"PLACEHOLDER","message":{"chain_id":900,"group_log":null,"log_type":"ListenerInterrupted","message":"NewRandomnessTaskListener is interrupted. Retry... Error: ContractClientError(FetchingRandomnessTaskError).","task_log":null,"transaction_receipt_log":null},"module_path":"arpa_node::listener","file":"crates/arpa-node/src/listener/mod.rs","line":40,"level":"ERROR","target":"arpa_node::listener","thread":"tokio-runtime-worker","thread_id":136545558255168,"node_id":"0x1234567890123456789012345678901234567890","l1_chain_id":900,"mdc":{},"node_info":"","group_info":"","version":"0.2.2"}'
TASK_RECEIVED = '{"time":"PLACEHOLDER","message":{"chain_id":900,"group_log":null,"log_type":"TaskReceived","message":"DKG grouping task received.","task_log":{"committer_id_address":null,"request_id":"0x","task_json":{"assignment_block_height":95,"coordinator_address":"0x8daf17a20c9dba35f005b6324f493785d239719d","epoch":1,"group_index":0,"members":["0xfabb0ac9d68b0b445fb7357272ff202c5651694a","0x71be63f3384f5fb98995898a86b02fb2426c5788","0xbcd4042de499d14e55001ccbb24a551f3b954096"],"size":3,"threshold":3},"task_type":"DKG"},"transaction_receipt_log":null},"module_path":"arpa_node::listener::pre_grouping","file":"crates/arpa-node/src/listener/pre_grouping.rs","line":82,"level":"INFO","target":"arpa_node::listener::pre_grouping","thread":"tokio-runtime-worker","thread_id":136545566660160,"node_id":"0x1234567890123456789012345678901234567890","l1_chain_id":900,"mdc":{},"node_info":"","group_info":"","version":"0.2.2"}'
def create_log_stream_if_not_exists():
    try:
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            logStreamNamePrefix=log_stream_name
        )
        
        streams = response.get('logStreams', [])
        if not any(stream['logStreamName'] == log_stream_name for stream in streams):
            raise ClientError({'Error': {'Code': 'ResourceNotFoundException'}}, 'DescribeLogStreams')
        
        print(f"Log stream '{log_stream_name}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            try:
                logs_client.create_log_stream(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name
                )
                print(f"Log stream '{log_stream_name}' created.")
            except ClientError as create_error:
                print(f"Failed to create log stream: {str(create_error)}")
                raise
        else:
            print(f"Error checking log stream: {str(e)}")
            raise

def add_log_messages(messages, keyword=None):
    events = []
    for message in messages:
        if keyword:
            message = message.replace('PLACEHOLDER', keyword)
        events.append({
            'timestamp': int(time.time() * 1000),
            'message': message
        })
    
    logs_client.put_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        logEvents=events
    )
    print(f"{len(events)} log messages added.")

if __name__ == "__main__":
    try:
        create_log_stream_if_not_exists()

        messages = [
            LISTENER_INTERRUPTED,
            TASK_RECEIVED
        ]
        keyword = datetime.now(timezone(timedelta(hours=8))).isoformat()
        add_log_messages(messages, keyword)

    except Exception as e:
        print(f"An error occurred: {str(e)}")