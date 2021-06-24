
INSERT INTO ORGANIZATION(id, fides_key, version_stamp, description) values (2, "Ethyca", 0, "An account modelling Ethyca systems");

INSERT INTO REGISTRY(id, organization_id, fides_key, name, description) values(1,1,"test", "Test registry", "A registry for testing setups");
INSERT INTO REGISTRY(id, organization_id, fides_key, name, description) values(2,2,"es", "Test ES registry", "A test registry for modelling ES");

INSERT INTO SYSTEM_OBJECT(id, organization_id, fides_key, version_stamp, fides_system_type, description, declarations, system_dependencies, datasets)
values (1,1,'test_system_1',0, 'SYSTEM','some test system',
        '[{ "name":"a","dataCategories":["telemetry_data"], "dataUse":"provide", "dataQualifier":"aggregated_data", "dataSubjectCategories":[] }]','[]', '[]');


INSERT INTO SYSTEM_OBJECT(id, organization_id, fides_key,version_stamp, fides_system_type, description, declarations, system_dependencies, datasets)
values (2,1,'test_system_2',0,'SYSTEM','some other test system',
        '[{ "name":"b","dataCategories":["end_user_identifiable_information", "personal_data_of_children"], "dataUse":"provide", "dataQualifier":"identified_data", "dataSubjectCategories":[] }]','[]','[]');


INSERT INTO POLICY(id, organization_id, version_stamp, fides_key, description) values (1,1,0,'test policy 1', 'random policy');

INSERT INTO POLICY_RULE(id, policy_id, organization_id, fides_key, description, data_categories, data_subject_categories, data_uses, data_qualifier, action)
values (1,1,1,'test_policy_rule_1', 'random rule 1', '{"inclusion":"ANY","values":[ ]}','{"inclusion":"ANY","values":[ ]}',
        '{"inclusion":"NONE","values":[ "provide" ]}','unlinked_pseudonymized_data','REQUIRE');
INSERT INTO POLICY_RULE(id, policy_id, organization_id, fides_key, description, data_categories, data_subject_categories, data_uses, data_qualifier, action)
values (2,1,1,'test_policy_rule_2', 'random rule 2', '{"inclusion":"ANY","values":[ "customer_content_data" ]}','{"inclusion":"ANY","values":[ "customer" ]}',
        '{"inclusion":"ANY","values":[ "provide" ]}','identified_data','REJECT');

INSERT INTO USER(id, organization_id, user_name, first_name, last_name, role) values (1,1,'demo1','Iama','Sample','ADMIN');

INSERT INTO APPROVAL( organization_id, system_id, user_id, version_stamp, status, action) values (1,1,1,0,'PASS','test data');

INSERT INTO DATASET(id, organization_id, fides_key, version_stamp, name, dataset_location, dataset_type) values (1,1,"test-dataset",0, "my test dataset", "us-east-1", "SQL");
INSERT INTO DATASET_TABLE(id, dataset_id, name) values (1,1, "table1");
INSERT INTO DATASET_TABLE(id, dataset_id, name) values (2,1, "table2");
INSERT INTO DATASET_FIELD(dataset_table_id, name, data_categories, data_qualifier) values (1,"field1", '["credentials"]',"aggregated_data");
INSERT INTO DATASET_FIELD(dataset_table_id, name, data_categories, data_qualifier) values (1,"field2", "[]","pseudonymized_data");
