import { Pool } from 'pg';

const { DATABASE_HOST, DATABASE_PORT, DATABASE_USER, DATABASE_PASSWORD, DATABASE_DB } = process.env;

const pool = new Pool({
  host: DATABASE_HOST || "localhost",
  port: Number(DATABASE_PORT) || 5432,
  user: DATABASE_USER || "postgres",
  password: DATABASE_PASSWORD || "postgres",
  database: DATABASE_DB || "postgres_example",
});

export default pool;