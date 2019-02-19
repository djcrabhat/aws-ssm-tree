from treelib import Tree, Node
import boto3
import click

region_name = None
path_separator = '/'

@click.command()
@click.option("--path", "-p", required=True, help="The hierarchy for the parameter. Hierarchies start with a forward slash (/) and end with the parameter name. Here is an example of a hierarchy: /Servers/Prod")
@click.option("--no-recursion", is_flag=True, help="Prevents recursion into descending levels.")
@click.option("--region", help="Specifies which AWS Region to send this request to.")
@click.version_option(message="aws-ssm-tree - version %(version)s")
@click.pass_context
def main(ctx, **kwargs):
    """
    SSM Tree is a tool that provides a tree visualization of the
    parameters hierarchy from AWS System Manager Parameter Store.
    """
    global region_name 

    path = kwargs.pop('path')
    recursive = not kwargs.pop('no_recursion')
    region_name = kwargs.pop('region')

    try:
        build_tree(path, recursive)
    except Exception as e:
        raise click.ClickException("{}".format(e))
    
def get_parameters(path=None, recursive=True):
    client = boto3.client('ssm', region_name=region_name)
    paginator = client.get_paginator('get_parameters_by_path')
    pages = paginator.paginate(
        Path = path,
        Recursive = recursive,
        WithDecryption = False
    )
    parameters = []
    for page in pages:
        parameters_page = [{"name": entry['Name'],
                           "type": entry['Type'],
                           "version": entry['Version']} for entry in page['Parameters']]
        parameters.extend(parameters_page)
    return parameters

def get_tree_from_path(path=None):
    path = path.split(path_separator)
    node_list = []
    for index, node in enumerate(path):
        if node:
            node_list.append({'node': node})
    for index, node in enumerate(path):
        if index == 1:
            node_list[index-1]['parent'] = None
        else:
            node_list[index-1]['parent'] = node_list[index-2]['node']
    return node_list

def build_tree(path, recursive):
    parameters = []
    for parameter in get_parameters(path, recursive):
        parameters.append(parameter['name'])
    tree = Tree()
    for item in parameters:
        for node in get_tree_from_path(item):
            try:
                tree.create_node(node['node'],node['node'],parent=node['parent'])
            except:
                pass
    if not tree:
        print("Nothing to show.")
    else:
        return tree.show()