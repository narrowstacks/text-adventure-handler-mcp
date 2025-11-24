# Text Adventure Web UI

This is a web interface for the Text Adventure Handler MCP. It runs in tandem with the MCP server, providing a visual dashboard for your adventures.

## Architecture

*   **Frontend:** React (Vite), Material-UI, Zustand, TanStack Query.
*   **Backend:** Node.js (Express), Better-SQLite3.
*   **Database:** Connects to the existing SQLite database used by the MCP server.

## Prerequisites

*   Docker and Docker Compose
*   The Text Adventure Handler MCP server should be initialized (so the database file exists).

## Running with Docker

1.  Navigate to the `web` directory:
    ```bash
    cd web
    ```

2.  Start the services:
    ```bash
    docker-compose up --build
    ```

3.  Open your browser to [http://localhost:3000](http://localhost:3000).

## Configuration

The `docker-compose.yml` file mounts the default database path:
`~/.text-adventure-handler/adventure_handler.db`

If your database is located elsewhere, update the `volumes` section in `docker-compose.yml`.

## Development

### Backend

```bash
cd web/backend
npm install
npm run dev
```
Runs on port 3001.

### Frontend

```bash
cd web/frontend
npm install
npm run dev
```
Runs on port 5173 (proxies `/api` to port 3001).
