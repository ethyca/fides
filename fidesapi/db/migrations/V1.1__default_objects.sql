-- Default Objects
INSERT INTO "ORGANIZATION"(id, fides_key, description) values (1, 'default_organization', 'Default organization that contains all objects without another specified organization.');

INSERT INTO "REGISTRY"(id, organization_id, fides_key, name, description) values(1,1,'default_registry', 'Default Registry', 'A default registry.');

INSERT INTO "USER"(id, organization_id, user_name, first_name, last_name, role, api_key) values (1,1,'default','default','default','ADMIN','test_api_key');
