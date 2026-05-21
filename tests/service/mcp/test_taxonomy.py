from fides.service.mcp.taxonomy import TenantTaxonomy


def test_taxonomy_known_data_use_passes():
    t = TenantTaxonomy.from_fideslang_defaults()
    assert t.is_known_data_use("essential.service.operations")


def test_taxonomy_unknown_data_use_rejected():
    t = TenantTaxonomy.from_fideslang_defaults()
    assert not t.is_known_data_use("not_a_real_use")


def test_taxonomy_hierarchical_category_match_parent():
    t = TenantTaxonomy.from_fideslang_defaults()
    assert t.is_known_data_category("user.contact")
    assert t.is_known_data_category("user.contact.email")


def test_allowed_data_categories_lists_fideslang_keys():
    t = TenantTaxonomy.from_fideslang_defaults()
    cats = t.allowed_data_categories()
    assert "user.contact.email" in cats
    assert any(c.startswith("user.") for c in cats)


def test_allowed_data_uses_lists_fideslang_keys():
    t = TenantTaxonomy.from_fideslang_defaults()
    uses = t.allowed_data_uses()
    assert any(u.startswith("essential.") for u in uses)


def test_allowed_data_subjects_lists_fideslang_keys():
    t = TenantTaxonomy.from_fideslang_defaults()
    subjects = t.allowed_data_subjects()
    assert "customer" in subjects
