from typing import List, Set

import pytest

from fides.api.util.taxonomy_utils import find_undeclared_categories


class TestFindUndeclaredCategories:
    @pytest.mark.parametrize(
        "input_categories, declared_categories, expected_output",
        [
            (
                {"user.contact.email"},
                {"user.contact.email"},
                [],
            ),
            (
                {"user.contact.email"},
                {"user.contact"},
                [],
            ),
            (
                {"user.contact.email"},
                {"user"},
                [],
            ),
            (
                {"user.contact.email"},
                {"user.contact.address"},
                ["user.contact.email"],
            ),
            (
                {
                    "user.government_id.passport_number",
                    "user.health_and_medical.genetic",
                },
                {"user.government_id"},
                ["user.health_and_medical.genetic"],
            ),
        ],
    )
    def test_find_undeclared_categories(
        self,
        input_categories: Set[str],
        declared_categories: Set[str],
        expected_output: List[str],
    ):
        assert (
            sorted(find_undeclared_categories(input_categories, declared_categories))
            == expected_output
        )

    def test_find_undeclared_categories_empty_input(self):
        assert find_undeclared_categories(set(), {"user.contact", "user.name"}) == []

    def test_find_undeclared_categories_empty_declared(self):
        assert sorted(
            find_undeclared_categories(
                {"user.contact.email", "user.financial.credit_card"}, set()
            )
        ) == ["user.contact.email", "user.financial.credit_card"]

    def test_find_undeclared_categories_no_undeclared(self):
        input_categories = {"user.contact.email", "user.name.first", "user.name.last"}
        declared_categories = {"user.contact", "user.name", "user.financial"}
        assert find_undeclared_categories(input_categories, declared_categories) == []

    def test_find_undeclared_categories_all_undeclared(self):
        input_categories = {
            "user.contact.email",
            "user.name.first",
            "user.financial.bank_account",
        }
        declared_categories = {"user.government_id", "user.health_and_medical"}
        assert sorted(
            find_undeclared_categories(input_categories, declared_categories)
        ) == [
            "user.contact.email",
            "user.financial.bank_account",
            "user.name.first",
        ]
