"""
Creates data visualizations for the data category hierarchy
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import Generator, List

FIDES_KEY_NAME = 'fides_key'
FIDES_PARENT_NAME = 'parent_key'


def category_sunburst_plot(categories: List[dict],
                           json_out: bool = False) -> str:
    """
    Create a sunburst plot from data categories yaml file
    Reference: https://plotly.com/python/sunburst-charts/
    Args:
        categories: list of the dictionaries for each taxonomy member
        json_out:

    Returns:
        Json representation of the figure if `json_out` is True, html otherwise
    """

    # add color map
    for c in categories:
        c['color'] = c[FIDES_KEY_NAME].split('.')[0]

    fig = px.sunburst(categories,
                      names=FIDES_KEY_NAME,
                      parents=FIDES_PARENT_NAME,
                      color='color'
                      )
    fig.update_layout(title_text="Fides Data Category Hierarchy", font_size=10)

    if json_out:
        return fig.to_json()
    return fig.to_html()


def category_sankey_plot(categories: List[dict],
                         json_out: bool = False) -> str:
    """
    Create a sankey plot from data categories yaml file
    Reference: https://plotly.com/python/sankey-diagram/
    Args:
        categories: list of the dictionaries for each taxonomy member
        json_out:

    Returns:
        Json representation of the figure if `json_out` is True, html otherwise
    """

    fides_key_dict = {v[FIDES_KEY_NAME]: i for i, v in enumerate(categories)}
    source = []
    target = []

    for c in categories:
        if FIDES_PARENT_NAME in c.keys():
            if c[FIDES_PARENT_NAME]:
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

    fig.update_layout(title_text="Fides Data Category Hierarchy", font_size=10)

    if json_out:
        return fig.to_json()
    return fig.to_html()


def convert_categories_to_nested_dict(categories: List[dict]) -> dict:
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

    def nested_dict(data: dict, keys: List) -> None:
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
                    # we've reached the end of the path (no more children)
                    data[key] = {}
                data = data[key]
            else:
                data[key] = {}

    nested_output = {}
    for c in categories:
        if FIDES_PARENT_NAME not in c:
            nested_output[c[FIDES_KEY_NAME]] = {}
        else:
            category_path = c[FIDES_KEY_NAME].split('.')
            nested_dict(nested_output, category_path)
    return nested_output


def nested_categories_to_html_list(categories: List[dict],
                                   indent: int = 1) -> str:
    """
    Create an HTML string unordered list from the keys of a nested dictionary
    Args:
        categories: list of the dictionaries for each taxonomy member
        indent: spacing multiplier

    Returns:

    """
    nested_categories = convert_categories_to_nested_dict(categories)

    def nest_to_html(nested_dict, indent_factor) -> Generator:
        """
        Create the html
        Args:
            nested_dict: nested dictionary for keys to convert to html list object
            indent_factor: spacing multiplier

        Returns:
            HTML string containing a nested, unordered list of the nested dictionary keys
        """
        spacing = '   ' * indent_factor
        for k, v in nested_dict.items():
            yield '{}<li>{}</li>'.format(spacing, k)
            if isinstance(v, dict):
                yield '{}<ul>\n{}\n{}</ul>'.format(
                    spacing,
                    "\n".join(nest_to_html(v, indent_factor + 1)),
                    spacing
                )
    header = '<h2>Fides Data Category Hierarchy</h2>'
    categories_tree = '\n'.join(nest_to_html(nested_categories, indent))
    return f'{header}\n{categories_tree}'
