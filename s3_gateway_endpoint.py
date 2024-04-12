import boto3

def create_s3_gateway_endpoint(vpc_id, route_table_ids, client):
    # Try to create an S3 gateway endpoint for the specified VPC and handle any exceptions
    try:
        # Create the VPC endpoint for Amazon S3
        response = client.create_vpc_endpoint(
            VpcEndpointType='Gateway',  # Specifies the endpoint type as a Gateway
            VpcId=vpc_id,  # The VPC ID where the endpoint will be created
            ServiceName=f'com.amazonaws.{boto3.session.Session().region_name}.s3',
            RouteTableIds=route_table_ids
        )
        # Extract the endpoint ID from the response
        endpoint_id = response['VpcEndpoint']['VpcEndpointId']
        print(f'Created S3 gateway endpoint {endpoint_id} for VPC {vpc_id}.')
        return endpoint_id
    except Exception as e:
        # Print an error message if the endpoint creation fails
        print(f'Error creating S3 gateway endpoint for VPC {vpc_id}: {e}')
        return None

def get_route_table_ids(vpc_id, client):
    # Retrieve all route table IDs associated with the specified VPC and handle exceptions
    try:
        # Describe route tables filtered by VPC ID
        response = client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        # Extract and return route table IDs from the response
        return [rt['RouteTableId'] for rt in response['RouteTables']]
    except Exception as e:
        # Print an error message if the operation fails
        print(f'Error retrieving route tables for VPC {vpc_id}: {e}')
        return []

def modify_route_tables(vpc_endpoint_id, route_table_ids, client):
    response = client.modify_vpc_endpoint(
        VpcEndpointId=vpc_endpoint_id,
        AddRouteTableIds=route_table_ids
    )
    return response

def main():
    # Create an EC2 client using Boto3
    client = boto3.client('ec2')
    # Describe all VPCs in the account/region
    vpcs = client.describe_vpcs()['Vpcs']

    # Iterate through each VPC
    for vpc in vpcs:
        vpc_id = vpc['VpcId']
        print(f'Checking VPC {vpc_id} for existing S3 gateway endpoints...')

        # Check if an S3 endpoint already exists in the VPC
        response = client.describe_vpc_endpoints(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'service-name', 'Values': [f'com.amazonaws.{boto3.session.Session().region_name}.s3']}
            ]
        )
        endpoints = response['VpcEndpoints']

        # Retrieve all route table IDs for the VPC
        route_table_ids = get_route_table_ids(vpc_id, client)

        # If an endpoint exists, print a message and skip to the next VPC
        if endpoints:
            print(f'S3 gateway endpoint already exists for VPC {vpc_id}. Updating route tables')
            endpoint_id = endpoints[0]['VpcEndpointId']
            modify_route_tables(endpoint_id, route_table_ids, client)
            continue
        else:
            # Create an S3 gateway endpoint for the VPC
            endpoint_id = create_s3_gateway_endpoint(vpc_id, route_table_ids, client)
            print(f'Created endpoint {endpoint_id}')
            continue

if __name__ == "__main__":
    main()