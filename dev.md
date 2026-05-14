# Running Novel Studio (Development)

## Start backend

```bash
cd app/backend
bash start.sh
```

The backend runs on `http://localhost:8765`.
On first run it installs Python dependencies and initialises `data/app.db`.

## Start frontend (Tauri dev)

In a second terminal:

```bash
cd app/frontend
npm run tauri dev
```

This starts Vite on port 1420 and opens the Tauri desktop window.

## Verify backend manually

```bash
curl http://localhost:8765/health
# {"status":"ok"}

curl http://localhost:8765/projects
# []

curl -X POST http://localhost:8765/projects \
  -H "Content-Type: application/json" \
  -d '{"title":"My Novel","genre":"literary fiction","pov":"third limited","tense":"past"}'
```

## Import the existing writing_system framework

```bash
curl -X POST http://localhost:8765/projects/import \
  -H "Content-Type: application/json" \
  -d '{"folder_path":"/media/nick/1TB_Storage1/projects/writing/writing_system"}'
```

## Prerequisites

- Python 3.11+
- Node 18+ / npm
- Rust + Cargo (for Tauri)
- `webkit2gtk-4.1` and `libjavascriptcoregtk-4.1` (Debian/Ubuntu):

```bash
sudo apt install libwebkit2gtk-4.1-dev libjavascriptcoregtk-4.1-dev \
  librsvg2-dev libssl-dev libgtk-3-dev libayatana-appindicator3-dev
```
