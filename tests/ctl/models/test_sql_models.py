from fides.api.models.sql_models import PrivacyDeclaration
from fides.api.db.system import get_system


def test_system_privacy_declarations_in_alphabetical_order(db, system):
    """
    Ensure that the system privacy declarations are in alphabetical order by name
    """
    # Add more privacy declarations to the system
    new_privacy_declarations = [
        {
            "data_use": "marketing.advertising.profiling",
            "name": "Declaration Name",
            "system_id": system.id,
        },
        {
            "data_use": "essential",
            "name": "Another Declaration Name",
            "system_id": system.id,
        }
    ]
    for data in new_privacy_declarations:
        PrivacyDeclaration.create(db=db, data=data)
        db.commit()

    db.refresh(system)
    updated_system = get_system(db, system.fides_key)

    privacy_declarations = updated_system.privacy_declarations
    sorted_privacy_declarations = sorted(privacy_declarations, key=lambda x: x.name)

    assert privacy_declarations == sorted_privacy_declarations, "Privacy declarations are not in alphabetical order by name"
