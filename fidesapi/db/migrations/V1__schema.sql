CREATE FUNCTION update_last_update_time_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
  BEGIN
    NEW.last_update_time = NOW();
    RETURN NEW;
  END;
$$;

CREATE TABLE if NOT EXISTS "ORGANIZATION" (
    id BIGSERIAL PRIMARY KEY,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT DEFAULT 0,
    "name" VARCHAR(100),
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_org_key UNIQUE(fides_key)
);
CREATE TRIGGER organization_last_update_time_trigger BEFORE UPDATE ON "ORGANIZATION" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

CREATE TABLE IF NOT EXISTS "SYSTEM_OBJECT"(
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    registry_id INT,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    metadata JSON,
    "name" VARCHAR(100),
    description VARCHAR(1000),
    system_type VARCHAR(100),
    system_dependencies JSON NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_system_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);
CREATE TRIGGER system_object_last_update_time_trigger BEFORE UPDATE ON "SYSTEM_OBJECT" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

CREATE TABLE IF NOT EXISTS "PRIVACY_DECLARATION"(
    id BIGSERIAL PRIMARY KEY,
    system_id BIGINT NOT NULL,
    "name" VARCHAR(100),
    data_categories JSON NOT NULL,
    data_use VARCHAR(100),
    data_qualifier VARCHAR(100),
    data_subjects JSON NOT NULL,
    dataset_references JSON NOT NULL,
    raw_datasets JSON NOT NULL,
    FOREIGN KEY (system_id) REFERENCES "SYSTEM_OBJECT"(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "REGISTRY" (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    metadata JSON,
    "name" VARCHAR(100),
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_registry_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);
CREATE TRIGGER registry_last_update_time_trigger BEFORE UPDATE ON "REGISTRY" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

CREATE TABLE IF NOT EXISTS "POLICY" (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    "name" VARCHAR(100),
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_policy_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);
CREATE TRIGGER policy_last_update_time_trigger BEFORE UPDATE ON "POLICY" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

CREATE TABLE IF NOT EXISTS "POLICY_RULE" (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    policy_id BIGINT NOT NULL REFERENCES "POLICY"(id) ON DELETE CASCADE,
    fides_key VARCHAR(100) NOT NULL,
    "name" VARCHAR(100),
    description VARCHAR(1000),
    data_categories JSON NOT NULL,
    data_uses JSON NOT NULL,
    data_subjects JSON NOT NULL,
    data_qualifier VARCHAR(100),
    "action" VARCHAR(100) NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_policy_rule_fides_key UNIQUE (fides_key, policy_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id),
    FOREIGN KEY (policy_id) REFERENCES "POLICY"(id) ON DELETE CASCADE
);
CREATE TRIGGER policy_rule_last_update_time_trigger BEFORE UPDATE ON "POLICY_RULE" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

CREATE TABLE IF NOT EXISTS "USER"(
    id              BIGSERIAL PRIMARY KEY,
    organization_id BIGINT          NOT NULL,
    user_name       VARCHAR(100) NOT NULL,
    first_name      VARCHAR(50),
    last_name       VARCHAR(50),
    "role"          VARCHAR(50) NOT NULL,
    api_key         VARCHAR(100) NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_name UNIQUE (user_name, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE

);
CREATE TRIGGER user_last_update_time_trigger BEFORE UPDATE ON "USER" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

CREATE TABLE IF NOT EXISTS "APPROVAL"(
    id              BIGSERIAL PRIMARY KEY,
    organization_id BIGINT          NOT NULL,
    "action" VARCHAR(50),
    system_id INT,
    registry_id INT,
    user_id BIGINT NOT NULL, -- TODO_REFERENCES USER(id),
    version_stamp BIGINT,
    submit_tag VARCHAR(100),
    submit_message VARCHAR(1000),
    status VARCHAR(50) NOT NULL,
    details JSON,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "AUDIT_LOG"(
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL, -- TODO_REFERENCES USER(id),
    "action" VARCHAR(20),
    version_stamp BIGINT,
    type_name VARCHAR(255),
    "from_value" JSON,
    "to_value" JSON,
    "change" JSON,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);
-- ------------------------------
--  Dataset
-- ------------------------------

CREATE TABLE IF NOT EXISTS "DATASET"(
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    metadata JSON,
    "name" VARCHAR(100),
    description VARCHAR(1000),
    data_categories JSON,
    data_qualifier VARCHAR(100),
    location VARCHAR(100),
    dataset_type VARCHAR(50),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_dataset_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);
CREATE TRIGGER dataset_last_update_time_trigger BEFORE UPDATE ON "DATASET" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();


CREATE TABLE IF NOT EXISTS "DATASET_FIELD"(
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "path" VARCHAR(1000),
    description VARCHAR(1000),
    data_categories JSON,
    data_qualifier  VARCHAR(100),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES "DATASET"(id) ON DELETE CASCADE
);
CREATE TRIGGER dataset_field_last_update_time_trigger BEFORE UPDATE ON "DATASET_FIELD" FOR EACH ROW EXECUTE PROCEDURE update_last_update_time_column();

-- ------------------------------
--  Taxonomy types
-- ------------------------------
CREATE TABLE IF NOT EXISTS "DATA_SUBJECT" (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    parent_id INT,
    parent_key VARCHAR(100),
    fides_key VARCHAR(100) NOT NULL,
    "name" VARCHAR(100),
    description VARCHAR(2000),
    CONSTRAINT unique_subject_category_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "DATA_CATEGORY" (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    parent_id INT,
    parent_key VARCHAR(100),
    fides_key VARCHAR(100) NOT NULL,
    "name" VARCHAR(100),
    clause VARCHAR(100),
    description VARCHAR(2000),
    CONSTRAINT unique_data_category_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "DATA_USE" (
     id BIGSERIAL PRIMARY KEY,
     organization_id BIGINT,
    parent_id INT,
    parent_key VARCHAR(100),
     fides_key VARCHAR(100) NOT NULL,
     "name" VARCHAR(100),
     clause VARCHAR(100),
     description VARCHAR(2000),
     CONSTRAINT unique_data_use_fides_key UNIQUE (fides_key, organization_id),
     FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "DATA_QUALIFIER" (
     id BIGSERIAL PRIMARY KEY,
     organization_id BIGINT,
     parent_id INT,
    parent_key VARCHAR(100),
     fides_key VARCHAR(100) NOT NULL,
     "name" VARCHAR(100),
     clause VARCHAR(100),
     description VARCHAR(2000),
     CONSTRAINT unique_data_qualifier_fides_key UNIQUE (fides_key, organization_id),
     FOREIGN KEY (organization_id) REFERENCES "ORGANIZATION"(id) ON DELETE CASCADE
);
