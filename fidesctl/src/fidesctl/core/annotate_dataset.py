"""
This script is a utility for interactively annotating data categories in the dataset manifest
"""

import pathlib
import webbrowser
from typing import Union, List

import click

from fidesctl.core import parse as core_parse
from fidesctl.core import visualize
from fideslang import manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField


class AnnotationAbortError(Exception):
    """
    Custom exception to handle mid annotation abort
    """
    pass


def get_data_categories_annotation(dataset_member: Union[Dataset, DatasetCollection, DatasetField]) -> List[str]:
    """
    Request the user's input to supply a list of data categories

    TODO: data_category validation would be nice. to let them know if what they've provided is okay

    Args:
        dataset_member: A member of a dataset [dataset, collection, field]

    Returns:
        List of the user's input
    """
    msg = f'''Enter comma separated data categories for [{dataset_member.name}] [Enter: skip, q: quit]'''
    user_categories = []
    user_response = click.prompt(msg, default=None)
    if user_response.lower() == 'q':
        if click.confirm('Are you sure you want to quit annotating the dataset? (progress will be saved)'):
            raise AnnotationAbortError
    if user_response:
        user_categories = [i.strip() for i in user_response.split(',')]
        # future: loop through inputs and validate
    return user_categories


def annotate_dataset(dataset_file: str,
                     dataset_key: str = 'dataset',
                     resource_type: str = 'data_category',
                     auto_open: bool = True,
                     annotate_all: bool = False,
                     file_split: bool = True):
    """
    Given a dataset.yml-like file, walk the user through an interactive cli to provide data categories
    for members of the dataset that do not have any specified
    Args:
        dataset_file: the file name for the dataset to annotate
        dataset_key: the primary dataset key
        resource_type: the type of data resource to point to for assistance (via visualization web page)
        auto_open: flag to attempt to automatically open the resource visualization web page
        annotate_all: flag to annotate all members of a dataset (default False: only annotate fields)
        file_split: flag to split multiple datasets into individual, self-named dataset yaml files

    Returns:
        Write the amended dataset file in place
    """
    output_filename = dataset_file

    # Make the user aware of the data_categories visualizer
    visualize_graphs_url = visualize.get_visualize_url(resource_type, 'graphs')
    visualize_text_url = visualize.get_visualize_url(resource_type, 'text')

    click.secho(f"""For reference, open the data category visualizer at either:
        {visualize_graphs_url}
        {visualize_text_url}
    """, fg='green')
    if auto_open:
        webbrowser.open(visualize_graphs_url, new=2)

    # load in the dataset
    datasets = core_parse.ingest_manifests(dataset_file)[dataset_key]

    # loop through each of the items in the dataset
    if len(datasets) > 1:
        if file_split:
            print(f'{len(datasets)} datasets present, individual files will be written!')
        print(f'{len(datasets)} datasets present, output files will be overwritten!')

    for dataset in datasets:  # iterate through each database/schema found
        current_dataset = Dataset(**dataset)
        click.secho(f'\n####\nAnnotating Dataset: [{current_dataset.name}]')

        if file_split:
            output_filename = str(pathlib.Path(output_filename).parents[0].joinpath(f'{current_dataset.name}.yml'))

        if annotate_all and not current_dataset.data_categories:
            click.secho(f'Database [{current_dataset.name}] has no data categories')
            current_dataset.data_categories = get_data_categories_annotation(current_dataset)

        for table in current_dataset.collections:
            click.secho(f'####\nAnnotating Table: [{table.name}]\n')
            if annotate_all and not table.data_categories:
                click.secho(f'Table [{table.name}] has no data categories')
                table.data_categories = get_data_categories_annotation(table)

            for field in table.fields:
                if not field.data_categories:
                    click.secho(f'Field [{table.name}.{field.name}] has no data categories')
                    try:
                        user_categories = get_data_categories_annotation(field)
                        click.secho(f'''Setting data categories for {table.name}.{field.name} to:
                        {user_categories}\n''')
                        field.data_categories = user_categories
                    except AnnotationAbortError:
                        break
            else:
                continue
            break
        else:
            continue
        # write each file
        manifests.write_manifest(output_filename,
                                 current_dataset.dict(),
                                 'dataset')
