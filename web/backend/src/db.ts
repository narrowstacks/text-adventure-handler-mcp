import Database from 'better-sqlite3';
import path from 'path';
import os from 'os';
import fs from 'fs';

// Align env var with the Python server: prefer DB_PATH, then ADVENTURE_DB_PATH, then HOST_DB_PATH.
// Expand ~ if provided so shell-style paths work in dev mode.
const resolvePath = (p: string) => p.startsWith('~') ? path.join(os.homedir(), p.slice(1)) : path.resolve(p);
const envDbPath = process.env.DB_PATH || process.env.ADVENTURE_DB_PATH || process.env.HOST_DB_PATH;
const DB_PATH = envDbPath ? resolvePath(envDbPath) : path.join(os.homedir(), '.text-adventure-handler', 'adventure_handler.db');

console.log(`Connecting to database at: ${DB_PATH}`);

// Ensure directory exists if we were to write, but we are read-only mostly.
// However, better-sqlite3 throws if file doesn't exist and we don't provide options?
// Actually, let's check existence.
if (!fs.existsSync(DB_PATH)) {
  console.warn(`Warning: Database file not found at ${DB_PATH}. The application may crash if you try to query data.`);
}

// Open in read-only mode if possible, or just default. 
// The prompt asked for "read-only", better-sqlite3 has { readonly: true } option.
const db = new Database(DB_PATH, { readonly: true, fileMustExist: false }); // fileMustExist: false allows opening, but queries will fail if empty? No, it creates if not exists unless readonly is set. 
// If readonly: true, it must exist. 
// Let's try to open it. If it fails, we handle it.

export default db;
