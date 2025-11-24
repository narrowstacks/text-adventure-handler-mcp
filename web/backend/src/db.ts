import { Database } from 'bun:sqlite';
import path from 'path';
import os from 'os';
import fs from 'fs';

const resolvePath = (p: string) => (p.startsWith('~') ? path.join(os.homedir(), p.slice(1)) : path.resolve(p));
const envDbPath = process.env.DB_PATH || process.env.ADVENTURE_DB_PATH || process.env.HOST_DB_PATH;
export const DB_PATH = envDbPath ? resolvePath(envDbPath) : path.join(os.homedir(), '.text-adventure-handler', 'adventure_handler.db');

const dir = path.dirname(DB_PATH);
if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

if (!fs.existsSync(DB_PATH)) {
  console.warn(`Database file not found at ${DB_PATH}. An empty file will be created.`);
  fs.closeSync(fs.openSync(DB_PATH, 'a'));
}

const db = new Database(DB_PATH, { readonly: true });
export default db;
