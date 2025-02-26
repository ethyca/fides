from fides.api.schemas.consentable_item import ConsentableItem, merge_consentable_items


class TestConsentableItemUtils:
    def test_merge_consentable_items_single_level(self):
        api_values = [
            ConsentableItem(
                type="Channel",
                external_id="1",
                name="Email",
                children=[
                    ConsentableItem(
                        type="MessageType", external_id="1", name="Welcome"
                    ),
                    ConsentableItem(
                        type="MessageType", external_id="2", name="Promotional"
                    ),
                ],
            )
        ]
        db_values = [
            ConsentableItem(
                type="Channel",
                external_id="2",
                name="SMS",
                children=[
                    ConsentableItem(
                        type="MessageType", external_id="1", name="Welcome"
                    ),
                    ConsentableItem(
                        type="MessageType", external_id="2", name="Transactional"
                    ),
                ],
            )
        ]
        assert merge_consentable_items(api_values, db_values) == [
            ConsentableItem(
                external_id="1",
                type="Channel",
                name="Email",
                notice_id=None,
                children=[
                    ConsentableItem(
                        external_id="1",
                        type="MessageType",
                        name="Welcome",
                        notice_id=None,
                        children=[],
                        unmapped=True,
                    ),
                    ConsentableItem(
                        external_id="2",
                        type="MessageType",
                        name="Promotional",
                        notice_id=None,
                        children=[],
                        unmapped=True,
                    ),
                ],
                unmapped=True,
            )
        ]

    def test_merge_consentable_items_nested(self):
        api_values = [
            ConsentableItem(
                type="Channel",
                external_id="1",
                name="Marketing",
                children=[
                    ConsentableItem(
                        type="MessageType", external_id="1", name="Newsletter"
                    ),
                    ConsentableItem(
                        type="MessageType", external_id="3", name="Promotional"
                    ),
                ],
            )
        ]
        db_values = [
            ConsentableItem(
                type="Channel",
                external_id="1",
                notice_id="notice_123",
                name="Marketing",
                children=[
                    ConsentableItem(
                        type="MessageType",
                        external_id="1",
                        name="Newsletter",
                        notice_id="notice_456",
                    ),
                    ConsentableItem(
                        type="MessageType", external_id="3", name="Transactional"
                    ),
                ],
            )
        ]
        assert merge_consentable_items(api_values, db_values) == [
            ConsentableItem(
                external_id="1",
                type="Channel",
                name="Marketing",
                notice_id="notice_123",
                children=[
                    ConsentableItem(
                        external_id="1",
                        type="MessageType",
                        name="Newsletter",
                        notice_id="notice_456",
                        children=[],
                        unmapped=False,
                    ),
                    ConsentableItem(
                        external_id="3",
                        type="MessageType",
                        name="Promotional",
                        notice_id=None,
                        children=[],
                        unmapped=False,
                    ),
                ],
                unmapped=False,
            )
        ]

    def test_merge_consentable_items_with_empty_list(self):
        api_values = [
            ConsentableItem(
                type="Channel",
                external_id="1",
                name="Email",
                children=[
                    ConsentableItem(type="MessageType", external_id="1", name="Welcome")
                ],
            )
        ]
        assert merge_consentable_items(api_values, []) == [
            ConsentableItem(
                external_id="1",
                type="Channel",
                name="Email",
                notice_id=None,
                children=[
                    ConsentableItem(
                        external_id="1",
                        type="MessageType",
                        name="Welcome",
                        notice_id=None,
                        children=[],
                        unmapped=True,
                    )
                ],
                unmapped=True,
            )
        ]

    def test_merge_consentable_items_with_none_value(self):
        api_values = [
            ConsentableItem(
                type="Channel",
                external_id="1",
                name="Email",
                children=[
                    ConsentableItem(type="MessageType", external_id="1", name="Welcome")
                ],
            )
        ]
        assert merge_consentable_items(api_values, None) == [
            ConsentableItem(
                external_id="1",
                type="Channel",
                name="Email",
                notice_id=None,
                children=[
                    ConsentableItem(
                        external_id="1",
                        type="MessageType",
                        name="Welcome",
                        notice_id=None,
                        children=[],
                        unmapped=True,
                    )
                ],
                unmapped=True,
            )
        ]

    def test_merge_consentable_items_multiple_items(self):
        api_values = [
            ConsentableItem(type="Channel", external_id="1", name="Email"),
            ConsentableItem(type="Channel", external_id="2", name="SMS"),
            ConsentableItem(type="Channel", external_id="3", name="Push"),
        ]
        db_values = [
            ConsentableItem(type="Channel", external_id="1", name="Email"),
            ConsentableItem(type="Channel", external_id="3", name="Push"),
            ConsentableItem(type="Channel", external_id="4", name="Web"),
        ]
        assert merge_consentable_items(api_values, db_values) == [
            ConsentableItem(
                external_id="1",
                type="Channel",
                name="Email",
                notice_id=None,
                children=[],
                unmapped=False,
            ),
            ConsentableItem(
                external_id="2",
                type="Channel",
                name="SMS",
                notice_id=None,
                children=[],
                unmapped=True,
            ),
            ConsentableItem(
                external_id="3",
                type="Channel",
                name="Push",
                notice_id=None,
                children=[],
                unmapped=False,
            ),
        ]
