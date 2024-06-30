#!/usr/bin/env python
import os
import yaml
import json
import time

from time import sleep
from eth_account import Account
from web3 import Web3
from prometheus_client import start_http_server, REGISTRY, Info, Enum, Gauge

config_path = 'exporter-config.yml'
w3 = None
node_registry_contract = None
controller_contract = None
config = {}
addresses = {}

def read_config():
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file)
            global config
            config = data
    else:
        print('Config file not found')

def read_addresses():
    with open('addresses.json', 'r') as file:
        data = json.load(file)
        for item in data:
            if item["ChainId"] == config['chain_id'] or int(item["ChainId"]) == config['chain_id']:
                global addresses
                addresses = item["Addresses"]
                break
            else:
                print("ChainId" + config['chain_id'] + "not found.")

def set_node_registry_contract():    
    node_registry_address = addresses['NodeRegistry']
    with open('abi/node-registry.json', 'r') as abi_file:
        contract_abi = json.load(abi_file)
    global node_registry_contract
    node_registry_contract = w3.eth.contract(address=node_registry_address, abi=contract_abi)

def set_controller_contract():
    controller_address = addresses['Controller']
    with open('abi/controller.json', 'r') as abi_file:
        contract_abi = json.load(abi_file)
    global controller_contract
    controller_contract = w3.eth.contract(address=controller_address, abi=contract_abi)

def initialize():
    read_config()
    read_addresses()
    global w3
    w3 = Web3(Web3.HTTPProvider(config['provider_endpoint']))
    set_node_registry_contract()
    set_controller_contract()

def get_node():
    result = node_registry_contract.functions.getNode(config['node_address']).call()
    return result    

def get_belonging_group():
    result = controller_contract.functions.getBelongingGroup(config['node_address']).call()
    return result

def get_group(index):
    result = controller_contract.functions.getGroup(index).call()
    return result

def get_coordinator(index):
    result = controller_contract.functions.getCoordinator(index).call()
    return result

if __name__ == '__main__':
    initialize() 
    start_http_server(config['chain_exporter_port'])      

    address_info = Info('node_address', 'Node address of current node client')
    address_info.info({'node_address': config['node_address']})

    node_status_enum = Enum('node_status', 'Status of node',
                states=['down', 'up'])
    group_index_gauge = Gauge('group_index', 'Index of the group')
    group_size_gauge = Gauge('group_size', 'Number of members in the group')
    group_state_enum = Enum('group_state', 'Status of node',
                states=['down', 'up'])
    committers_gauge = Gauge('committers', 'List of committers', ['item'])
    dkg_state_enum = Enum('DKG_state', 'Status of DKG Process',
                states=['finished', 'processing'])

    print('Server started')

    while True:
        print('Fetchin data')
        # get on-chain data
        node_info = get_node()
        group_index = get_belonging_group()[0]
        if group_index != -1:
            print('Group index found')
            group_info = get_group(group_index)
            coordinator = get_coordinator(group_index)

        print('Updating metrics')
        # node state
        if node_info[2]:
            node_status_enum.state('up')
        else:
            node_status_enum.state('down')

        if group_index != -1:
            #group index
            group_index_gauge.set(group_index)

            #group size
            group_size_gauge.set(group_info[2])

            # group state
            if group_info[-2]:
                group_state_enum.state('up')
            else:
                group_state_enum.state('down')

            # committers
            for committer in group_info[-4]:
                committers_gauge.labels(item=committer).set(1)

            # DKG status
            if coordinator == '0x0000000000000000000000000000000000000000':
                dkg_state_enum.state('finished')
            else:
                dkg_state_enum.state('processing')

        time.sleep(config['interval'])
    