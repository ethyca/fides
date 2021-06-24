
CREATE TABLE if NOT EXISTS ORGANIZATION (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT DEFAULT 0,
    `name` VARCHAR(100),
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_org_key UNIQUE(fides_key)
);

CREATE TABLE IF NOT EXISTS SYSTEM_OBJECT(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT NOT NULL,
    registry_id INT,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    fides_system_type VARCHAR(100),
    `name` VARCHAR(100),
    description VARCHAR(1000),
    declarations JSON NOT NULL,
    system_dependencies JSON NOT NULL,
    datasets JSON NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_system_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS REGISTRY (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT NOT NULL,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    `name` VARCHAR(100),
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_registry_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS POLICY (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT NOT NULL,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    `name` VARCHAR(100),
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_policy_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS POLICY_RULE (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT NOT NULL,
    policy_id BIGINT NOT NULL REFERENCES POLICY(id) ON DELETE CASCADE,
    fides_key VARCHAR(100) NOT NULL,
    `name` VARCHAR(100),
    description VARCHAR(1000),
    data_categories JSON NOT NULL,
    data_uses JSON NOT NULL,
    data_subject_categories JSON NOT NULL,
    data_qualifier VARCHAR(100),
    `action` VARCHAR(100) NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_policy_rule_fides_key UNIQUE (fides_key, policy_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id),
    FOREIGN KEY (policy_id) REFERENCES POLICY(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS USER(
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT          NOT NULL,
    user_name       VARCHAR(100) NOT NULL,
    first_name      VARCHAR(50),
    last_name       VARCHAR(50),
    `role`            VARCHAR(50) NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_name UNIQUE (user_name, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE

);

CREATE TABLE IF NOT EXISTS APPROVAL(
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT          NOT NULL,
    `action` VARCHAR(50),
    system_id INT,
    registry_id INT,
    user_id BIGINT NOT NULL, -- TODO_REFERENCES USER(id),
    version_stamp BIGINT,
    submit_tag VARCHAR(100),
    submit_message VARCHAR(1000),
    status VARCHAR(50) NOT NULL,
    details JSON,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AUDIT_LOG(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    object_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL, -- TODO_REFERENCES USER(id),
    `action` VARCHAR(20),
    version_stamp BIGINT,
    type_name VARCHAR(255),
    `from_value` JSON,
    `to_value` JSON,
    `change` JSON,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);
-- ------------------------------
--  Dataset
-- ------------------------------


CREATE TABLE IF NOT EXISTS DATASET(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT NOT NULL,
    fides_key VARCHAR(100) NOT NULL,
    version_stamp BIGINT,
    `name` VARCHAR(100),
    description VARCHAR(1000),
    dataset_location VARCHAR(100),
    dataset_type VARCHAR(50),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_dataset_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS DATASET_TABLE(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_id BIGINT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    description VARCHAR(1000),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_dataset_table_name UNIQUE (name, dataset_id),
    FOREIGN KEY (dataset_id) REFERENCES DATASET(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS DATASET_FIELD(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_table_id BIGINT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    description VARCHAR(1000),
    data_categories JSON,
    data_qualifier  VARCHAR(100),
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_table_id) REFERENCES DATASET_TABLE(id) ON DELETE CASCADE
);

-- ------------------------------
--  Taxonomny types
-- ------------------------------
CREATE TABLE IF NOT EXISTS DATA_SUBJECT_CATEGORY (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT,
    parent_id INT,
    fides_key VARCHAR(100) NOT NULL,
    `name` VARCHAR(100),
    description VARCHAR(2000),
    CONSTRAINT unique_subject_category_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS DATA_CATEGORY (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    organization_id BIGINT,
    parent_id INT,
    fides_key VARCHAR(100) NOT NULL,
    `name` VARCHAR(100),
    clause VARCHAR(100),
    description VARCHAR(2000),
    CONSTRAINT unique_data_category_fides_key UNIQUE (fides_key, organization_id),
    FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS DATA_USE (
     id BIGINT PRIMARY KEY AUTO_INCREMENT,
     organization_id BIGINT,
     parent_id INT,
     fides_key VARCHAR(100) NOT NULL,
     `name` VARCHAR(100),
     clause VARCHAR(100),
     description VARCHAR(2000),
     CONSTRAINT unique_data_use_fides_key UNIQUE (fides_key, organization_id),
     FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS DATA_QUALIFIER (
     id BIGINT PRIMARY KEY AUTO_INCREMENT,
     organization_id BIGINT,
     parent_id INT,
     fides_key VARCHAR(100) NOT NULL,
     `name` VARCHAR(100),
     clause VARCHAR(100),
     description VARCHAR(2000),
     CONSTRAINT unique_data_qualifier_fides_key UNIQUE (fides_key, organization_id),
     FOREIGN KEY (organization_id) REFERENCES ORGANIZATION(id) ON DELETE CASCADE
);
