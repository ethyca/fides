"""
Author: Brenton Mallen
Email: brenton@ethyca.com
Company: Ethyca Data Inc.
Created: 9/30/21
"""

from fideslang import manifests
import plotly.express as px
import plotly.graph_objects as go

FIDES_KEY_NAME = 'fides_key'
FIDES_PARENT_NAME = 'parent_key'


def get_taxonomy_categories(taxonomy_path: str,
                            category_key: str = 'data_category') -> list[dict]:
    manifests = manifests.ingest_manifests(taxonomy_path)
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
