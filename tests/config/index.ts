import * as dotenv from 'dotenv';
import path from 'path';
import { Client } from 'pg'

// Build the path to the .env file
const envFilePath = path.resolve(process.cwd(), `config/.env`);
dotenv.config({ path: envFilePath });

// Export the database configuration
export const dbConfig = {
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
};

export const dbClient = new Client(dbConfig);

export const defaultUser = {
  username: process.env.DEFAULT_USERNAME,
  password: process.env.DEFAULT_PASSWORD
}

export const testUser = {
  username: process.env.TEST_USERNAME,
  bad_username: process.env.TEST_FAILED_USERNAME,
  password: process.env.TEST_PASSWORD
}

export const testName = `${testUser.username}${process.env.TEST_WORKER_INDEX}`;
export const testBadName = `${testUser.bad_username}${process.env.TEST_WORKER_INDEX}`;
export const testPassword = `${testUser.password}${process.env.TEST_WORKER_INDEX}`
export const testmail = `${testName}@test.com`;

export const username = defaultUser.username;
export const password = defaultUser.password;