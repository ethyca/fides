from typing import Set

from pygtrie import StringTrie


def find_undeclared_categories(
    input_categories: Set[str], declared_categories: Set[str]
) -> Set[str]:
    """
    Finds the categories in input_categories that are not declared in the given list of declared categories.

    This function uses a trie-based approach to perform hierarchical matching of categories. It considers
    a category as declared if it matches any of the following conditions:
    - The category itself is present in the declared categories.
    - Any parent category of the category is present in the declared categories.

    For example, if "user.contact.email" is in input_categories and the declared categories contain
    "user.contact" or "user", then "user.contact.email" will be considered as declared.
    """

    declared_trie = StringTrie(separator=".")
    for category in declared_categories:
        declared_trie[category] = True

    undeclared_categories = set()
    for category in input_categories:
        prefix, _ = declared_trie.longest_prefix(category)
        if not prefix:
            undeclared_categories.add(category)

    return undeclared_categories
