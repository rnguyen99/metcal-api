# Metcal Asset API

FastAPI service that authenticates users, issues JWT tokens, and exposes CRUD-style endpoints for managing assets in a SQLite database.

## Prerequisites
- Python 3.10+
- (Optional) `virtualenv` or `venv` for isolated installs

## Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables if needed (see `config.py` for the full list such as `DATABASE_URL`, `JWT_SECRET`, `CORS_ALLOW_ORIGINS`).
4. Initialize the SQLite database and seed demo data:
   ```bash
   .venv/bin/python init_db.py
   ```

## Running the API
```bash
.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Logs are written under `logs/` based on the settings in `logger.py`.

## Testing with curl
1. **Obtain a token**
   ```bash
   curl -X POST http://localhost:8000/api/token \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'
   ```
   Save the `access_token` from the JSON response.

2. **List assets**
   ```bash
   curl http://localhost:8000/api/assets \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Create an asset**
   ```bash
   curl -X POST http://localhost:8000/api/asset \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Router"}'
   ```

4. **Fetch an asset**
   ```bash
   curl http://localhost:8000/api/asset/1 \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

5. **Update an asset**
   ```bash
   curl -X PUT http://localhost:8000/api/asset/1 \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Updated Router"}'
   ```

## Deploying to IIS with HttpPlatformHandler
1. **Install prerequisites** on the Windows Server host:
   - Add the IIS Web Server role with the `HttpPlatformHandler` feature (available via Microsoft Web Platform Installer or the “IIS: Application Development” feature set).
   - Install Python 3.10+ system-wide; ensure the Visual C++ redistributable for your Python release is present.
2. **Lay down the app** in a folder such as `D:\apps\metcal-api`:
   ```powershell
   cd D:\apps
   git clone <repo-url> metcal-api
   cd metcal-api
   py -3 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python init_db.py
   ```
   Create a writable `logs` directory if it does not already exist.
3. **Configure environment** expected by [config.py](config.py). For IIS you can either:
   - Set system-level environment variables (e.g., `setx DATABASE_URL "sqlite:///D:/apps/metcal-api/asset.db"`).
   - Or add `<environmentVariables>` entries inside [web.config](web.config) next to the existing `PYTHONPATH` entry.
4. **Review/update web.config** paths:
   - `processPath` must point to `.venv\Scripts\python.exe` within your deployment directory.
   - Update the `arguments` and log file paths if you deploy somewhere other than `D:\apps\metcal-api`.
5. **Create the IIS site**:
   - In IIS Manager add a new Website with the physical path set to your deployment folder and bindings set to the desired host/port.
   - Use an Application Pool set to “No Managed Code”, 64-bit (or match your Python build), and disable “Start Automatically” until after configuration.
6. **Start the site and verify**:
   - Start the Application Pool then the Website. IIS launches Uvicorn via HttpPlatformHandler, proxying external requests to the internal `%HTTP_PLATFORM_PORT%`.
   - Tail `logs/httpplatform.log` plus the FastAPI logs under `logs/` for troubleshooting.
   - Hit `http://<server-host>/api/assets` with curl/Postman to confirm the API responds.

## Next Steps
- Add automated tests (e.g., with `pytest`) and document how to run them.
- Extend the API contract in `models.py` if new fields are required.
