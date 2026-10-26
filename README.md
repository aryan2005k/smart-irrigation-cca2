# Smart Multizone IoT Irrigation and Crop Monitoring System

Student-friendly CCD CCA2 project with Flask dashboard, three zones, SQLite history, simulated readings, ESP32 HTTP endpoint/sketch, Docker, Jenkins template and tests.

## Prototype limitation
Default readings are simulated. Dashboard Start/Stop controls update software state only and do not operate physical pumps. The ESP32 example sends sensor readings but does not control a pump. Add local fail-safe logic and suitable hardware protection before real-world use.

## Run locally (Windows PowerShell)
```powershell
cd smart-irrigation-cca2
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. If activation is blocked:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Tests
```powershell
pytest -q
```

## Docker
```powershell
docker build -t smart-irrigation-cca2:local .
docker run --rm -p 5000:5000 -v irrigation-data:/app/data smart-irrigation-cca2:local
```
Open http://127.0.0.1:5000.

## Pages and API
- `/` dashboard; `/zones` controls; `/health` health check
- `GET /api/zones`, `/api/summary`, `/api/history`, `/api/logs`
- `PATCH /api/zones/1` with `{"threshold":30,"mode":"auto"}`
- `POST /api/zones/1/control` with `{"action":"start"}` or `{"action":"stop"}`
- `POST /api/simulate` generates demo readings
- `POST /api/iot/readings` accepts `{"zone_id":1,"moisture":28.5,"temperature":26.2}`

## ESP32 setup
Open `iot/esp32_irrigation.ino` in Arduino IDE, set Wi-Fi details and a reachable server URL, calibrate raw sensor values, select your ESP32 board and upload. The ESP32 and server must be able to reach each other; `127.0.0.1` on the ESP32 is not your computer.

## Jenkins/AWS template
`Jenkinsfile` is a starter template requiring setup:
1. Create ECR repository `smart-irrigation-cca2` in `ap-south-1`.
2. Jenkins agent needs Python, Docker, AWS CLI and SSH.
3. Configure Jenkins credential IDs: `aws-credentials` (AWS credentials), `aws-account-id` (12-digit account ID secret text), `irrigation-ec2-host` (EC2 host secret text), `irrigation-ec2-ssh` (SSH private key).
4. EC2 needs Docker, AWS CLI, permission to pull from ECR (prefer an EC2 IAM role), and suitable security-group rules.
5. Review deployment commands and add an actual post-deploy health check/rollback for your environment. The template assumes a Linux Jenkins agent and Ubuntu EC2; adjust to your plugins.
6. Never commit credentials to GitHub.

## Security and safety
This classroom app has no authentication. Add authentication, authorization, HTTPS and device authentication before public exposure. Physical irrigation needs isolation, fusing, waterproofing, dry-run protection and maximum run-time limits. Never connect a pump directly to an ESP32 GPIO.
