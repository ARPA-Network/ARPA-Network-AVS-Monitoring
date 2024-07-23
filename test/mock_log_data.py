import boto3
import time
import random
import uuid

from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

region = 'us-east-1'

logs_client = boto3.client('logs', region_name=region)
log_group_name = 'arpa-network-logs'
log_stream_name = 'NODE_ADDRESS_PLACEHOLDER'
LISTENER_INTERRUPTED = '{"time":"TIME_PLACEHOLDER","message":{"chain_id":900,"group_log":null,"log_type":"ListenerInterrupted","message":"NewRandomnessTaskListener is interrupted. Retry... Error: ContractClientError(FetchingRandomnessTaskError).","task_log":null,"transaction_receipt_log":null},"module_path":"arpa_node::listener","file":"crates/arpa-node/src/listener/mod.rs","line":40,"level":"ERROR","target":"arpa_node::listener","thread":"tokio-runtime-worker","thread_id":136545558255168,"node_id":"NODE_ADDRESS_PLACEHOLDER","l1_chain_id":900,"mdc":{},"node_info":"","group_info":"","version":"0.2.2"}'
TASK_RECEIVED = '{"time":"TIME_PLACEHOLDER","message":{"chain_id":900,"group_log":null,"log_type":"TaskReceived","message":"DKG grouping task received.","task_log":{"committer_id_address":null,"request_id":"REQUEST_ID_PLACEHOLDER","task_json":{"assignment_block_height":95,"coordinator_address":"0x8daf17a20c9dba35f005b6324f493785d239719d","epoch":1,"group_index":0,"members":["0xfabb0ac9d68b0b445fb7357272ff202c5651694a","0x71be63f3384f5fb98995898a86b02fb2426c5788","0xbcd4042de499d14e55001ccbb24a551f3b954096"],"size":3,"threshold":3},"task_type":"DKG"},"transaction_receipt_log":null},"module_path":"arpa_node::listener::pre_grouping","file":"crates/arpa-node/src/listener/pre_grouping.rs","line":82,"level":"INFO","target":"arpa_node::listener::pre_grouping","thread":"tokio-runtime-worker","thread_id":136545566660160,"node_id":"NODE_ADDRESS_PLACEHOLDER","l1_chain_id":900,"mdc":{},"node_info":"","group_info":"","version":"0.2.2"}'
SIGNATURE_FINISHED = '{"time":"TIME_PLACEHOLDER","message":{"chain_id":900,"group_log":null,"log_type":"PartialSignatureFinished","message":"Partial signature generated.","task_log":{"committer_id_address":null,"request_id":"REQUEST_ID_PLACEHOLDER","task_json":{"assignment_block_height":220,"callback_gas_limit":97213,"callback_max_gas_price":"3000006","group_index":0,"params":"0x","request_confirmations":1,"request_id":"REQUEST_ID_PLACEHOLDER","request_type":"Randomness","requester":"0xb7f8bc63bbcad18155201308c8f3540b07f84f5e","seed":"28802578433952080325955980021437715071830272288048947941140244031708629812839","subscription_id":1},"task_type":{"BLS":"Randomness"}},"transaction_receipt_log":null},"module_path":"arpa_node::subscriber::ready_to_handle_randomness_task","file":"crates/arpa-node/src/subscriber/ready_to_handle_randomness_task.rs","line":154,"level":"INFO","target":"arpa_node::subscriber::ready_to_handle_randomness_task","thread":"tokio-runtime-worker","thread_id":136545596077632,"node_id":"NODE_ADDRESS_PLACEHOLDER","l1_chain_id":900,"mdc":{"fn_name":"handle"},"node_info":"","group_info":"","version":"0.2.2"}'
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

def add_log_message(message, timestamp, request_id=None):
    events = []
    message = message.replace('TIME_PLACEHOLDER', timestamp)
    if request_id:
        message = message.replace('REQUEST_ID_PLACEHOLDER', request_id)
    events.append({
        'timestamp': int(time.time() * 1000),
        'message': message
    })
    
    logs_client.put_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        logEvents=events
    )
    print("log message added.")

def add_listener_interrupted(count):
    i = 0
    while i < count:
        timestamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
        add_log_message(LISTENER_INTERRUPTED, timestamp)
        i = i + 1 

def add_signature_processing(count):
    i = 0
    while i < count:
        finished_time = datetime.now(timezone(timedelta(hours=8)))
        random_seconds = random.randint(1, 100)
        random_string = str(uuid.uuid4())
        received_time = finished_time - timedelta(seconds=random_seconds)
        add_log_message(TASK_RECEIVED, received_time.isoformat(), str(random_seconds) + '-' + random_string)
        add_log_message(SIGNATURE_FINISHED, finished_time.isoformat(), str(random_seconds) + '-' + random_string)
        i = i + 1

def add_task_received(count):
    i = 0
    while i < count:
        timestamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
        random_string = str(uuid.uuid4())
        add_log_message(TASK_RECEIVED, timestamp, random_string)
        i = i + 1

if __name__ == "__main__":
    try:
        create_log_stream_if_not_exists()
        add_listener_interrupted(20)
        add_signature_processing(5)

    except Exception as e:
        print(f"An error occurred: {str(e)}")