import { Pool } from 'pg';

const { DATABASE_HOST, DATABASE_PORT, DATABASE_USER, DATABASE_PASSWORD, DATABASE_DB } = process.env;
if (!DATABASE_HOST) throw new Error('No DATABASE_HOST');
if (!DATABASE_PORT) throw new Error('No DATABASE_PORT');
if (!DATABASE_USER) throw new Error('No DATABASE_USER');
if (!DATABASE_PASSWORD) throw new Error('No DATABASE_PASSWORD');
if (!DATABASE_DB) throw new Error('No DATABASE_DB');

const pool = new Pool({
  host: DATABASE_HOST,
  port: +DATABASE_PORT,
  user: DATABASE_USER,
  password: DATABASE_PASSWORD,
  database: DATABASE_DB,
});

export default pool;