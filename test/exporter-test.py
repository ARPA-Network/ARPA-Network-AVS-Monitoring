import subprocess
import requests
import re
from web3 import Web3

NODE_ADDRESS = "0x1BD61FAAa74F7B2aAF414753B74d6070f821D16D"  
RPC_URL = "https://mainnet.gateway.tenderly.co/<API_KEY>"  
REGISTRY_ADDRESS = "0x58e39879374901e17A790af039DC9Ac06baCf25B" 
CONTROLLER_ADDRESS = "0xBcA1a9cA6B460E6B265DBcf7249b45BDdC381Dfd" 
CUSTOM_EXPORTER_URL = "http://localhost:8000"

def run_cast_call(contract_address, function_signature, *args):
    command = f'cast call {contract_address} "{function_signature}" {" ".join(args)} --rpc-url {RPC_URL}'
    # print(command)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_account_balance():
    command = f'cast balance {NODE_ADDRESS} --rpc-url {RPC_URL}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_prometheus_metric(metric_name):
    response = requests.get(f"{CUSTOM_EXPORTER_URL}/metrics")
    for line in response.text.split('\n'):
        if line.startswith(metric_name):
            return float(line.split()[1])
    return None

def get_prometheus_metrics():
    response = requests.get(f"{CUSTOM_EXPORTER_URL}/metrics")
    metrics = {}
    for line in response.text.split('\n'):
        if line and not line.startswith('#'):
            parts = line.split()
            if len(parts) >= 2:
                metric_name = parts[0].split('{')[0]
                value = float(parts[-1])
                if '{' in parts[0]:
                    label = parts[0].split('{')[1].split('}')[0]
                    metrics.setdefault(metric_name, {})[label] = value
                else:
                    metrics[metric_name] = value
    return metrics

def parse_cast_result(result, output_type):
    if output_type == 'bool':
        return result.lower() == 'true'
    elif output_type == 'int':
        return int(result, 16)
    elif output_type == 'address':
        return result.lower()
    else:
        return result

def test_eth_balance():
    cast_balance = float(Web3.from_wei(int(get_account_balance()), 'ether'))
    exporter_balance = get_prometheus_metric('eth_balance')
    print(f"ETH Balance - Cast: {cast_balance}, Exporter: {exporter_balance}")
    assert abs(cast_balance - exporter_balance) < 0.0001, "ETH balance mismatch"

def test_node_status():
    cast_result = run_cast_call(REGISTRY_ADDRESS, "getNode(address nodeAddress)((address,bytes,bool,bool,uint256))", NODE_ADDRESS)
    cast_status = parse_cast_result(cast_result.split(',')[2], 'bool')
    exporter_status = get_prometheus_metric('node_status') == 1  
    print(f"Node Status - Cast: {cast_status}, Exporter: {exporter_status}")
    assert cast_status == exporter_status, "Node status mismatch"

def test_group_index():
    cast_result = run_cast_call(CONTROLLER_ADDRESS, "getBelongingGroup(address)(int256,uint256)", NODE_ADDRESS)
    cast_group_index = parse_cast_result(cast_result.split('\n')[0], 'int')
    exporter_group_index = int(get_prometheus_metric('group_index'))
    print(f"Group Index - Cast: {cast_group_index}, Exporter: {exporter_group_index}")
    assert cast_group_index == exporter_group_index, "Group index mismatch"

def test_group_size():
    group_index = int(get_prometheus_metric('group_index'))
    if group_index != -1:
        cast_result = run_cast_call(CONTROLLER_ADDRESS, "getGroup(uint256 groupIndex)((uint256,uint256,uint256,uint256,(address,uint256[4])[],address[],(address[],(uint256,uint256[4],address[]))[],bool,uint256[4]))", str(group_index))
        cast_group_size = parse_cast_result(cast_result.split(',')[2], 'int')
        exporter_group_size = int(get_prometheus_metric('group_size'))
        print(f"Group Size - Cast: {cast_group_size}, Exporter: {exporter_group_size}")
        assert cast_group_size == exporter_group_size, "Group size mismatch"
    else:
        print("Node does not belong to any group, skipping group size test")

def test_group_state():
    group_index = int(get_prometheus_metric('group_index'))
    if group_index != -1:
        cast_result = run_cast_call(CONTROLLER_ADDRESS, "getGroup(uint256 groupIndex)((uint256,uint256,uint256,uint256,(address,uint256[4])[],address[],(address[],(uint256,uint256[4],address[]))[],bool,uint256[4]))", str(group_index))
        cast_group_state = parse_cast_result(cast_result.split(',')[-2], 'bool')
        exporter_group_state = get_prometheus_metric('group_state') == 1  # 1 for 'up', 0 for 'down'
        print(f"Group State - Cast: {cast_group_state}, Exporter: {exporter_group_state}")
        assert cast_group_state == exporter_group_state, "Group state mismatch"
    else:
        print("Node does not belong to any group, skipping group state test")

def test_coordinator():
    group_index = int(get_prometheus_metric('group_index'))
    if group_index != -1:
        cast_result = run_cast_call(CONTROLLER_ADDRESS, "getCoordinator(uint256)(address)", str(group_index))
        cast_coordinator = parse_cast_result(cast_result, 'address')
        
        dkg_state = get_prometheus_metric('DKG_state')
        
        if dkg_state == 1: 
            expected_coordinator = "0x0000000000000000000000000000000000000000"
        else:
            expected_coordinator = cast_coordinator
        
        print(f"Coordinator - Cast: {cast_coordinator}, Expected: {expected_coordinator}")
        assert cast_coordinator == expected_coordinator, "Coordinator mismatch"
    else:
        print("Node does not belong to any group, skipping coordinator test")

def parse_group_info(group_info_str):
    committers_match = re.search(r'\[(0x[a-fA-F0-9]+(?:,\s*0x[a-fA-F0-9]+)*)\]', group_info_str)
    
    if committers_match:
        committers_str = committers_match.group(1)
        committers = [addr.strip() for addr in committers_str.split(',')]
    else:
        committers = []

    return {
        'committers': committers
    }

def test_committers():
    group_index = int(get_prometheus_metrics()['group_index'])
    if group_index != -1:
        cast_result = run_cast_call(CONTROLLER_ADDRESS, "getGroup(uint256 groupIndex)((uint256,uint256,uint256,uint256,(address,uint256[4])[],address[],(address[],(uint256,uint256[4],address[]))[],bool,uint256[4]))", str(group_index))
        group_info = parse_group_info(cast_result)
        cast_committers = group_info['committers']
        prometheus_metrics = get_prometheus_metrics()
        exporter_committers = [
            committer.split('=')[1].strip('"')
            for committer, value in prometheus_metrics.get('committers', {}).items()
            if value == 1.0
        ]
        
        print(f"Committers - Cast: {cast_committers}")
        print(f"Committers - Exporter: {exporter_committers}")
        assert set(cast_committers) == set(exporter_committers), "Committers mismatch"
    else:
        print("Node does not belong to any group, skipping committers test")

def main():
    print("Starting tests...")
    test_eth_balance()
    test_node_status()
    test_group_index()
    test_group_size()
    test_group_state()
    test_coordinator()
    test_committers()
    print("All tests completed successfully!")

if __name__ == "__main__":
    main()