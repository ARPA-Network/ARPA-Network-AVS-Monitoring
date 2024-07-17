#!/bin/bash

# Function to read YAML file
parse_yaml() {
    local prefix=$2
    local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
    sed -ne "s|^\($s\):|\1|" \
         -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
         -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
    awk -F$fs '{
        indent = length($1)/2;
        vname[indent] = $2;
        for (i in vname) {if (i > indent) {delete vname[i]}}
        if (length($3) > 0) {
            vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
            printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
        }
    }'
}

# Read config file
eval $(parse_yaml config.yml)

# Check if required values are present
if [ -z "$node_address" ] || [ -z "$chain_id" ] || [ -z "$rpc_endpoint" ]; then
    echo "Error: Missing required values in config.yml"
    exit 1
fi

# Function to copy and replace content in files
copy_and_replace() {
    local src=$1
    local dest=$2
    
    # Create destination directory if it doesn't exist
    mkdir -p "$(dirname "$dest")"
    
    # Copy file
    cp "$src" "$dest"
    
    # Replace content
    sed -i "s|0x1234567890123456789012345678901234567890|$node_address|g" "$dest"
    sed -i "s|14000|$chain_id|g" "$dest"
    sed -i "s|https://mainnet.infura.io/v3/YOUR-PROJECT-ID|$rpc_endpoint|g" "$dest"
    
    echo "Processed file: $dest"
}

# Copy and replace content in custom-exporter-config-example.yml
copy_and_replace "custom-exporter/custom-exporter-config-example.yml" "exporter-config.yml"

# Copy and replace content in aws_exporter_config_example.yml
copy_and_replace "aws_exporter_config_example.yml" "aws_exporter_config.yml"

echo "Script completed successfully"