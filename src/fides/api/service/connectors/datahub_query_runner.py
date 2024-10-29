from typing import Optional, List

from datahub.ingestion.graph.client import DataHubGraph
from loguru import logger


class DatahubQueryRunner:
    """
    Class used to run graphQL queries against a Datahub instance.
    """

    def __init__(
        self, datahub_client: DataHubGraph, fides_categories_glossary_node: str
    ) -> None:
        self.datahub_client = datahub_client
        self.fides_categories_glossary_node = fides_categories_glossary_node
        self.fides_term_group_urn = self.get_or_create_fides_glossary_node_urn()

    def get_or_create_fides_glossary_node_urn(self) -> str:
        """
        Retrieves or creates the Fides term group. Returns the URN of the term group.
        """
        # Search for the glossary node by urn
        # Need to escape curly braces {} by doubling them
        search_nodes_query = f"""
            query search {{
                search(input: {{ type: GLOSSARY_NODE, query: "{self.fides_categories_glossary_node}" }}) {{
                    searchResults {{
                        entity {{
                            urn
                        }}
                    }}
                }}
            }}
        """

        raw_results = self.datahub_client.execute_graphql(search_nodes_query)
        results = raw_results["search"]["searchResults"]

        if len(results) > 1:
            logger.warning(
                f"Found multiple {self.fides_categories_glossary_node} DataHub glossary nodes. Using first result."
            )
        elif len(results) == 1:
            logger.info(
                f"Found existing {self.fides_categories_glossary_node} DataHub glossary node"
            )

        if results:
            return results[0]["entity"]["urn"]

        # Create the term group, since it doesn't exist
        logger.info(
            f"Creating {self.fides_categories_glossary_node} DataHub glossary node..."
        )
        create_node_query = f"""
            mutation createGlossaryNode {{
                createGlossaryNode(input: {{
                    id: "{self.fides_categories_glossary_node}",
                    name: "Fides Data Categories",
                    description: "Data Categories from the Fides taxonomy",
                }})
            }}
        """

        raw_results = self.datahub_client.execute_graphql(create_node_query)
        logger.info(
            f"Created {self.fides_categories_glossary_node} DataHub glossary node."
        )
        return raw_results["createGlossaryNode"]

    # TODO: use enum for entity type
    def get_entity_urn(self, entity_type: str, query_string: str) -> Optional[str]:
        # Build graphQL query to search for an entity by its ID.
        # The "filters" field is needed to do an exact match on the ID, because
        # otherwise the search will return partial matches as well.
        # E.g "user.contact" would return both "user.contact.email" and "user.contact"
        search_entity_query = f"""
            query search {{
                search(input: {{
                    type: {entity_type},
                    query: "{query_string}",
                    filters:  [{{
                        field: "id",
                        values: ["{query_string}"]
                    }}]
                }}) {{
                    searchResults {{
                        entity {{
                            urn
                        }}
                    }}
                }}
            }}
        """
        raw_results = self.datahub_client.execute_graphql(search_entity_query)
        results = raw_results["search"]["searchResults"]

        if not results:
            return None

        return results[0]["entity"]["urn"]

    def get_or_create_term(self, term_id: str, term_description: str) -> str:
        existing_term = self.get_entity_urn("GLOSSARY_TERM", term_id)

        if existing_term:
            logger.debug(f"Found existing term {term_id}")
            return existing_term

        create_term_query = f"""
            mutation createGlossaryTerm {{
                createGlossaryTerm(input: {{
                    id: "{term_id}",
                    name: "{term_id}",
                    description: "{term_description}",
                    parentNode: "{self.fides_term_group_urn}",
                }})
            }}
        """

        raw_results = self.datahub_client.execute_graphql(create_term_query)
        logger.debug(f"Created term {term_id}")
        return raw_results["createGlossaryTerm"]

    def add_terms_to_dataset_field(
        self, term_urns: List[str], dataset_urn: str, field_name
    ) -> None:
        """
        Adds a list of terms to a dataset field.
        If a term is already associated with the field, then it will not be added again.
        """
        terms_string = ", ".join([f'"{term_urn}"' for term_urn in term_urns])
        add_term_to_dataset_field_query = f"""
            mutation addTerms {{
                addTerms(
                input: {{
                    termUrns: [{terms_string}],
                    resourceUrn: "{dataset_urn}",
                    subResourceType:DATASET_FIELD,
                    subResource:"{field_name}"
                }})
            }}
        """

        self.datahub_client.execute_graphql(add_term_to_dataset_field_query)
