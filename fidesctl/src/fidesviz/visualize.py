"""
Author: Brenton Mallen
Email: brenton@ethyca.com
Company: Ethyca Data Inc.
Created: 9/30/21
"""

from fideslang.manifests import ingest_manifests
import plotly.express as px
import plotly.graph_objects as go

FIDES_KEY_NAME = 'fides_key'
FIDES_PARENT_NAME = 'parent_key'


def get_taxonomy_categories(taxonomy_path: str,
                            category_key: str = 'data_category') -> list[dict]:
    manifests = ingest_manifests(taxonomy_path)
    return manifests[category_key]


def category_sunburst_plot(taxonomy_path: str,
                           category_key: str = 'data_category',
                           json_out: bool = False) -> str:
    """
    Create a sunburst plot from data categories yaml file
    Reference: https://plotly.com/python/sunburst-charts/
    Args:
        taxonomy_path: full path fo the taxonomy directory
        category_key:
        json_out:

    Returns:
        Json representation of the figure if `json_out` is True, html otherwise
    """

    categories = get_taxonomy_categories(taxonomy_path, category_key)

    # add color map
    for c in categories:
        c['color'] = c[FIDES_KEY_NAME].split('.')[0]

    fig = px.sunburst(categories,
                      names='fides_key',
                      parents='parent_key',
                      color='color'
                      )
    fig.update_layout(title_text="Fides Data Category Hierarchy", font_size=10)

    if json_out:
        return fig.to_json()
    return fig.to_html()


def category_sankey_plot(taxonomy_path: str,
                         category_key: str = 'data_category',
                         json_out: bool = False) -> str:
    """
    Create a sunburst plot from data categories yaml file
    Reference: https://plotly.com/python/sunburst-charts/
    Args:
        taxonomy_path: full path fo the taxonomy directory
        category_key:
        json_out:

    Returns:
        Json representation of the figure if `json_out` is True, html otherwise
    """

    categories = get_taxonomy_categories(taxonomy_path, category_key)
    fides_key_dict = {v[FIDES_KEY_NAME]: i for i, v in enumerate(categories)}
    source = []
    target = []

    for c in categories:
        if 'parent_key' in c.keys():
            source.append(fides_key_dict[c[FIDES_PARENT_NAME]])
            target.append(fides_key_dict[c[FIDES_KEY_NAME]])

    fig = go.Figure(data=[go.Sankey(
        valueformat=".1f",
        valuesuffix="%",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=list(fides_key_dict.keys()),
            color="blue",  # Maybe make this 'ethyca blue'?
            hovertemplate='%{label}',
        ),
        link=dict(
            source=source,
            target=target,
            value=target
        ))])

    if json_out:
        return fig.to_json()
    return fig.to_html()


def convert_categories_to_nested_dict(categories: list[dict]) -> dict:
    """
    Convert a catalog yaml file into a hierarchical nested dictionary.
    Leaf nodes will have an empty dictionary as the value.

    e.g.:

    {Parent1:
        {
            Child1: {},
            Child2: {},
            Parent2: {
                Child3: {}
                }
        }
    }

    Args:
        categories : list of dictionaries containing each entry from a catalog yaml file

    Returns:

    """

    def nested_dict(data: dict, keys: list) -> None:
        """
        Create a nested dictionary given a list of strings as a key path
        Args:
            data: Dictionary to contain the nested dictionary as it's built
            keys: List of keys that equates to the 'path' down the nested dictionary

        Returns:
            None
        """
        for key in keys:
            if key in data:
                if key == keys[-1]:
                    data[key] = {}
                data = data[key]
            else:
                data[key] = {}

    nested_output = {}
    for c in categories:
        if FIDES_PARENT_NAME in c:
            nested_output[c[FIDES_PARENT_NAME]] = {}
        else:
            category_path = c[FIDES_PARENT_NAME].split('.')
            nested_dict(nested_output, category_path)
    return nested_output
