#!/usr/bin/env python
import os
import yaml
import json
import time
import logging
from typing import Dict, Any, Tuple, List
from web3.exceptions import ContractLogicError, InvalidAddress
from web3 import Web3
from prometheus_client import start_http_server, Info, Enum, Gauge
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

class CustomExporter:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.addresses: Dict[str, str] = {}
        self.w3 = None
        self.node_registry_contract = None
        self.controller_contract = None
        self.known_committers = set()
        self.last_processed_block = 19879870 #inital block on first event
        self.activation_events = []
        self.current_node_status = None
        self.last_activation_status_updated_at = None
        # Prometheus metrics
        self.address_info = Info('node_address', 'Node account address of current node client')
        self.eth_balance_gauge = Gauge('eth_balance', 'ETH balance of the node account address')
        self.node_status_enum = Enum('node_status', 'Status of node', states=['down', 'up'])
        self.fetch_times_gauge = Gauge('fetch_times', 'Times of Data Fetching')
        self.group_index_gauge = Gauge('group_index', 'Index of the group')
        self.group_size_gauge = Gauge('group_size', 'Number of members in the group')
        self.group_state_enum = Enum('group_state', 'Status of group', states=['down', 'up'])
        self.committers_gauge = Gauge('committers', 'List of committers', ['item'])
        self.dkg_state_enum = Enum('DKG_state', 'Status of DKG Process', states=['finished', 'processing', 'overrun'])
        self.uptime_gauge = Gauge('node_total_uptime', 'Total uptime of the node client in seconds', ['node_address'])
        self.task_received_gauge = Gauge('randcast_task_received', 'Randcast task received', ['l1_chain_id'])
        self.listener_interrupted_gauge = Gauge('randcast_listener_interrupted', 'Randcast listener interrupted', ['l1_chain_id'])
        self.partial_signature_generation_time_gauge = Gauge('randcast_partial_signature_generation_time', 'Randcast partial signature generation time', ['l1_chain_id'])


    def initialize(self):
        self.read_config()
        self.read_addresses()
        self.setup_web3()
        self.set_node_registry_contract()
        self.set_controller_contract()

    def fetch_data(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching data from {url}: Status code {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            return None
        
    def fetch_events(self, node_address, batch_size=100000):
        start_time = time.time() 
        event_definitions = [
            (self.node_registry_contract.events.NodeRegistered, 'nodeAddress'),
            (self.node_registry_contract.events.NodeActivated, 'nodeAddress'),
            (self.node_registry_contract.events.NodeQuit, 'nodeAddress'),
            (self.node_registry_contract.events.NodeSlashed, 'nodeIdAddress')
        ]

        new_events = []
        latest_block = self.w3.eth.get_block('latest')['number']
        
        for event, address_param_name in event_definitions:
            try:
                from_block = self.last_processed_block
                while True:
                    if from_block > latest_block:
                        break         
                    event_filter = event.create_filter(
                        fromBlock=from_block,
                        toBlock=from_block + batch_size - 1,  
                        argument_filters={address_param_name: node_address}
                    )
                    batch_events = event_filter.get_all_entries()
                    new_events.extend(batch_events)
                    
                    from_block += batch_size
            except Exception as e:
                print(f"Error fetching {event.event_name} events: {str(e)}")

        new_events.sort(key=lambda x: (x['blockNumber'], x['transactionIndex'], x['logIndex']))
        self.activation_events.extend(new_events)
        self.activation_events.sort(key=lambda x: (x['blockNumber'], x['transactionIndex'], x['logIndex']))

        if new_events:
            self.last_processed_block = new_events[-1]['blockNumber'] + 1
        
        end_time = time.time()  
        execution_time = end_time - start_time  

        # print(f"fetch_events execution time: {execution_time:.4f} seconds")
        # print(f"Total events fetched: {len(new_events)}")

    def calculate_uptime(self, node_address, node_status):
        total_uptime = 0
        current_start = None

        for event in self.activation_events:
            event_type = event['event']
            event_time = self.w3.eth.get_block(event['blockNumber'])['timestamp']

            if event_type in ['NodeRegistered', 'NodeActivated']:
                if current_start is None:
                    current_start = event_time
                self.last_activation_status_updated_at = event_time
            elif event_type in ['NodeQuit', 'NodeSlashed']:
                if current_start is not None:
                    total_uptime += event_time - current_start
                    current_start = None
                self.last_activation_status_updated_at = event_time

        if node_status:
            total_uptime += int(time.time()) - self.last_activation_status_updated_at

        self.uptime_gauge.labels(node_address=node_address).set(total_uptime)

    def update_uptime(self, node_address, node_status):
        self.fetch_events(node_address)
        self.calculate_uptime(node_address, node_status)

    def accumulate_uptime(self, node_address, node_status):
        if node_status:
            current_time = int(time.time())
            accumulated_time = current_time - self.last_activation_status_updated_at
            self.uptime_gauge.labels(node_address=node_address).inc(accumulated_time)
            self.last_activation_status_updated_at = current_time

    def update_aws_metrics(self, node_address):
        urls = [
            f"https://ynnnmyu5n1.execute-api.us-east-1.amazonaws.com/randcast-task-received?node_id={node_address}",
            f"https://fxxk2yesr0.execute-api.us-east-1.amazonaws.com/randcast-listener-interrupted?node_id={node_address}",
            f"https://3fxdughka1.execute-api.us-east-1.amazonaws.com/randcast-partial-signature-generation-time?node_id={node_address}"
        ]

        gauges = [self.task_received_gauge, self.listener_interrupted_gauge, self.partial_signature_generation_time_gauge]

        for url, gauge in zip(urls, gauges):
            result = self.fetch_data(url)
            if result:
                for item in result:
                    value = 0
                    if 'partial-signature-generation-time' in url:
                        value = item.get('average')
                    else: 
                        value = item.get('sum')
                    l1_chain_id = item['dimensions']['l1_chain_id']
                    gauge.labels(l1_chain_id=l1_chain_id).set(value)
            else:
                if 'listener-interrupted' in url:
                    gauge.labels(l1_chain_id=self.config['l1_chain_id']).set(0)

    def read_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        self.validate_config()

    def validate_config(self):
        required_keys = ['l1_chain_id', 'provider_endpoint', 'node_address', 'exporter_port', 'interval']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration: {key}")

    def read_addresses(self):
        try:
            with open('addresses.json', 'r') as file:
                data = json.load(file)
                for item in data:
                    if str(item["ChainId"]) == str(self.config['l1_chain_id']):
                        self.addresses = item["Addresses"]
                        return
                raise ValueError(f"ChainId {self.config['l1_chain_id']} not found in addresses.json")
        except FileNotFoundError:
            logger.error("addresses.json file not found")
            raise

    def setup_web3(self):
        self.w3 = Web3(Web3.HTTPProvider(self.config['provider_endpoint']))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
        self.config['node_address'] = self.w3.to_checksum_address(self.config['node_address'])

    def set_node_registry_contract(self):
        node_registry_address = self.addresses['NodeRegistry']
        with open('abi/node-registry.json', 'r') as abi_file:
            contract_abi = json.load(abi_file)
        self.node_registry_contract = self.w3.eth.contract(address=node_registry_address, abi=contract_abi)

    def set_controller_contract(self):
        controller_address = self.addresses['Controller']
        with open('abi/controller.json', 'r') as abi_file:
            contract_abi = json.load(abi_file)
        self.controller_contract = self.w3.eth.contract(address=controller_address, abi=contract_abi)

    def check_eth_balance(self) -> float:
        try:
            balance_wei = self.w3.eth.get_balance(self.config['node_address'])
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except InvalidAddress:
            logger.error(f"Invalid address: {self.config['node_address']}")
            return 0
        except Exception as e:
            logger.error(f"Error checking ETH balance: {e}")
            return 0
    
    def get_node(self) -> Tuple[str, bytes, bool, bool, int]:
        try:
            return self.node_registry_contract.functions.getNode(self.config['node_address']).call()
        except ContractLogicError as e:
            logger.error(f"Error calling getNode: {e}")
            raise

    def get_belonging_group(self) -> Tuple[int, int]:
        try:
            return self.controller_contract.functions.getBelongingGroup(self.config['node_address']).call()
        except ContractLogicError as e:
            logger.error(f"Error calling getBelongingGroup: {e}")
            raise

    def get_group(self, index: int) -> Tuple[int, int, int, int, List[Tuple[str, List[int]]], List[str], List[Tuple[List[str], Tuple[int, List[int], List[str]]]], bool, List[int]]:
        try:
            return self.controller_contract.functions.getGroup(index).call()
        except ContractLogicError as e:
            logger.error(f"Error calling getGroup: {e}")
            raise

    def get_coordinator(self, index: int) -> str:
        try:
            return self.controller_contract.functions.getCoordinator(index).call()
        except ContractLogicError as e:
            logger.error(f"Error calling getCoordinator: {e}")
            raise

    def get_phase(self, address: str) -> str:
        try:
            contract_abi = ''
            with open('abi/coordinator.json', 'r') as abi_file:
                contract_abi = json.load(abi_file)
            coordinator_contract = self.w3.eth.contract(address=address, abi=contract_abi)
            return coordinator_contract.functions.inPhase().call()
        except ContractLogicError as e:
            logger.error(f"Error calling get_phase: {e}")
            raise

    def update_metrics(self):
        try:
            node_info = self.get_node()            
            
            # Update node status
            self.node_status_enum.state('up' if node_info[3] else 'down')
            eth_balance = self.check_eth_balance()
            self.eth_balance_gauge.set(eth_balance)

            if(self.current_node_status and not node_info[3]):
                self.accumulate_uptime(self.config['node_address'], node_info[3])
            else:
                self.update_uptime(self.config['node_address'], node_info[3])
            self.current_node_status = node_info[3]

            group_index, _ = self.get_belonging_group()
            self.group_index_gauge.set(group_index)
            if group_index != -1:
                group_info = self.get_group(group_index)
                coordinator = self.get_coordinator(group_index)
                # Update group metrics                
                self.group_size_gauge.set(group_info[2])
                self.group_state_enum.state('up' if group_info[-2] else 'down')

                # Update committers
                for committer in self.known_committers:
                    self.committers_gauge.labels(item=committer).set(0)

                new_committers = set(group_info[-4])
                for committer in new_committers:
                    self.committers_gauge.labels(item=committer).set(1)

                self.known_committers = new_committers
                
                state = 'finished'
                if coordinator != ZERO_ADDRESS:
                    phase = self.get_phase(coordinator)
                    if phase != -1:
                        state = 'processing'
                    else: 
                        state = 'overrun'

                # Update DKG status
                self.dkg_state_enum.state(state)
            else:
                logger.warning("Node does not belong to any group")

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def run(self):
        counter = 0
        start_http_server(self.config['exporter_port'])
        self.address_info.info({'node_address': self.config['node_address'],'timestamp': str(int(time.time()))})
        logger.info('Exporter server started')
        # self.update_uptime(self.config['node_address'])

        while True:
            logger.info('Fetching data and updating metrics')
            self.update_metrics()
            self.update_aws_metrics(self.config['node_address'])
            self.fetch_times_gauge.set(counter)
            counter = counter + 1
            time.sleep(self.config['interval'])

if __name__ == '__main__':
    config_path = os.getenv('EXPORTER_CONFIG', 'exporter-config.yml')
    exporter = CustomExporter(config_path)
    
    try:
        exporter.initialize()
        exporter.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)