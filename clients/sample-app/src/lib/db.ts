import { Pool } from "pg";

// Load the DB configuration from ENV vars
const {
  FIDES_SAMPLE_APP__DATABASE_HOST: host,
  FIDES_SAMPLE_APP__DATABASE_PORT: port,
  FIDES_SAMPLE_APP__DATABASE_USER: user,
  FIDES_SAMPLE_APP__DATABASE_PASSWORD: password,
  FIDES_SAMPLE_APP__DATABASE_DB: db,
} = process.env;

// For backwards-compatibility, also support unprefixed versions
const {
  DATABASE_HOST,
  DATABASE_PORT,
  DATABASE_USER,
  DATABASE_PASSWORD,
  DATABASE_DB,
} = process.env;

const pool = new Pool({
  host: host || DATABASE_HOST || "localhost",
  port: Number(port || DATABASE_PORT || 5432),
  user: user || DATABASE_USER || "postgres",
  password: password || DATABASE_PASSWORD || "postgres",
  database: db || DATABASE_DB || "postgres_example",
});

export default pool;
