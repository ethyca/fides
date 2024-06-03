CREATE KEYSPACE IF NOT EXISTS app_keyspace WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
USE app_keyspace;

CREATE TABLE if not exists users (
    user_id UUID PRIMARY KEY,
    name TEXT,
    age INT,
    email TEXT
);

INSERT INTO users (user_id, name, age, email) VALUES (uuid(), 'John', 41, 'customer-1@example.com');
INSERT INTO users (user_id, name, age, email) VALUES (uuid(), 'Jane', 38, 'jane@example.com');
INSERT INTO users (user_id, name, age, email) VALUES (uuid(), 'Marguerite', 27, 'customer-2@example.com');
INSERT INTO users (user_id, name, age, email) VALUES (uuid(), 'Lafayette', 55, 'customer-3@example.com');
INSERT INTO users (user_id, name, age, email) VALUES (uuid(), 'Manuel', 23, 'customer-4@example.com');