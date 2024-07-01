#!/usr/bin/env python
import os
import yaml
import json
import time
import logging
from typing import Dict, Any, Tuple, List

from web3 import Web3
from web3.exceptions import ContractLogicError
from prometheus_client import start_http_server, Info, Enum, Gauge

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

        # Prometheus metrics
        self.address_info = Info('node_address', 'Node address of current node client')
        self.node_status_enum = Enum('node_status', 'Status of node', states=['down', 'up'])
        self.group_index_gauge = Gauge('group_index', 'Index of the group')
        self.group_size_gauge = Gauge('group_size', 'Number of members in the group')
        self.group_state_enum = Enum('group_state', 'Status of group', states=['down', 'up'])
        self.committers_gauge = Gauge('committers', 'List of committers', ['item'])
        self.dkg_state_enum = Enum('DKG_state', 'Status of DKG Process', states=['finished', 'processing'])

    def initialize(self):
        self.read_config()
        self.read_addresses()
        self.setup_web3()
        self.set_node_registry_contract()
        self.set_controller_contract()

    def read_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        self.validate_config()

    def validate_config(self):
        required_keys = ['chain_id', 'provider_endpoint', 'node_address', 'exporter_port', 'interval']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration: {key}")

    def read_addresses(self):
        try:
            with open('addresses.json', 'r') as file:
                data = json.load(file)
                for item in data:
                    if str(item["ChainId"]) == str(self.config['chain_id']):
                        self.addresses = item["Addresses"]
                        return
                raise ValueError(f"ChainId {self.config['chain_id']} not found in addresses.json")
        except FileNotFoundError:
            logger.error("addresses.json file not found")
            raise

    def setup_web3(self):
        self.w3 = Web3(Web3.HTTPProvider(self.config['provider_endpoint']))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")

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

    def get_group(self, index: int) -> Tuple[int, int, int, List[str], List[str], bool, bool]:
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

    def update_metrics(self):
        try:
            node_info = self.get_node()
            group_index, _ = self.get_belonging_group()

            # Update node status
            self.node_status_enum.state('up' if node_info[2] else 'down')

            if group_index != -1:
                group_info = self.get_group(group_index)
                coordinator = self.get_coordinator(group_index)

                # Update group metrics
                self.group_index_gauge.set(group_index)
                self.group_size_gauge.set(group_info[2])
                self.group_state_enum.state('up' if group_info[-2] else 'down')

                # Update committers
                for committer in group_info[-4]:
                    self.committers_gauge.labels(item=committer).set(1)

                # Update DKG status
                self.dkg_state_enum.state('finished' if coordinator == ZERO_ADDRESS else 'processing')
            else:
                logger.warning("Node does not belong to any group")

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def run(self):
        start_http_server(self.config['exporter_port'])
        self.address_info.info({'node_address': self.config['node_address']})
        
        logger.info('Exporter server started')

        while True:
            logger.info('Fetching data and updating metrics')
            self.update_metrics()
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