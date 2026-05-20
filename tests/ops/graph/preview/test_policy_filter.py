from fides.api.graph.preview.policy_filter import (
    _matches,
    filter_categories_by_targets,
)


def test_no_targets_returns_all():
    """targets=None means no filtering — all categories pass through."""
    categories = ["user.contact.email", "system.operations"]
    assert filter_categories_by_targets(categories, None) == categories


def test_empty_targets_returns_empty():
    """targets=set() short-circuits to empty list."""
    assert filter_categories_by_targets(["user.contact.email"], set()) == []


def test_exact_match():
    """Category equals a target exactly."""
    result = filter_categories_by_targets(
        ["user.contact.email"], {"user.contact.email"}
    )
    assert result == ["user.contact.email"]


def test_descendant_match():
    """user.contact.email matches target user.contact (ancestor)."""
    result = filter_categories_by_targets(["user.contact.email"], {"user.contact"})
    assert result == ["user.contact.email"]


def test_non_matching_dropped():
    """Category not in any target's subtree is dropped."""
    result = filter_categories_by_targets(
        ["system.operations", "user.contact.email"], {"user.contact"}
    )
    assert result == ["user.contact.email"]


def test_unknown_category_dropped_when_no_prefix_match():
    """A custom category not under any target is dropped."""
    result = filter_categories_by_targets(
        ["totally.made.up", "user.contact.email"], {"user.contact"}
    )
    assert result == ["user.contact.email"]


def test_custom_subcategory_matches_via_dot_prefix():
    """Custom categories not in the taxonomy match via dot-prefix fallback."""
    result = filter_categories_by_targets(
        ["user.contact.email.work_address", "user.contact.email"],
        {"user.contact"},
    )
    assert result == ["user.contact.email.work_address", "user.contact.email"]


def test_custom_subcategory_no_false_prefix_match():
    """Dot-prefix prevents 'user_provided' matching target 'user'."""
    result = filter_categories_by_targets(
        ["user_provided.identifiable.contact"], {"user"}
    )
    assert result == []


def test_custom_subcategory_exact_match():
    """Custom category that exactly equals a target is kept."""
    result = filter_categories_by_targets(["custom.analytics"], {"custom.analytics"})
    assert result == ["custom.analytics"]


def test_cycle_defense():
    """_matches terminates even if called with a cyclical parent map."""
    cyclic_parents = {"a": "b", "b": "c", "c": "a"}
    assert _matches("a", {"z"}, cyclic_parents) is False
