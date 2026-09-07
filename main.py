import os
import cv2
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from ultralytics import YOLO

load_dotenv()

app = FastAPI(title="Sistema de Inspección Industrial")

model = YOLO('best.pt')
esp32_ip = os.getenv("ESP32_IP")
esp32_url = f"http://{esp32_ip}:81/stream"

OS_SCRAP_DIR = "scrap"
os.makedirs(OS_SCRAP_DIR, exist_ok=True)

stats = {
    "total_ok": 0,
    "total_defective": 0,
    "last_status": "Esperando..."
}

defect_active = False
ok_active = False
frames_without_piece = 0
RESET_THRESHOLD_FRAMES = 10

def stream_pipeline():
    global defect_active, ok_active, frames_without_piece, stats
    
    cap = cv2.VideoCapture(esp32_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Error: No se pudo conectar con la ESP32-CAM.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(source=frame, conf=0.5, imgsz=640, verbose=False)
        annotated_frame = results[0].plot()

        has_defect = False
        has_ok = False

        for box in results[0].boxes:
            class_name = model.names[int(box.cls[0])].lower()
            if "cross_bad" in class_name:
                has_defect = True
                break
            elif "cross_ok" in class_name:
                has_ok = True

        if has_defect:
            frames_without_piece = 0
            stats["last_status"] = "⚠️ DEFECTO DETECTADO"

            if not defect_active:
                stats["total_defective"] += 1
                defect_active = True
                ok_active = True

                filename = f"{OS_SCRAP_DIR}/defecto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Foto de defecto guardada: {filename}")

        elif has_ok:
            frames_without_piece = 0
            stats["last_status"] = "✅ PIEZA OK"

            if not ok_active and not defect_active:
                stats["total_ok"] += 1
                ok_active = True

        else:
            if defect_active or ok_active:
                frames_without_piece += 1
                
                if frames_without_piece >= RESET_THRESHOLD_FRAMES:
                    defect_active = False
                    ok_active = False
                    frames_without_piece = 0
                    stats["last_status"] = "Esperando..."
                    print("🔄 Pieza retirada. Sistema listo.")

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        stream_pipeline(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/stats")
def get_stats():
    total = stats["total_ok"] + stats["total_defective"]
    yield_rate = (stats["total_ok"] / total * 100) if total > 0 else 100.0
    return {
        **stats,
        "total_inspected": total,
        "yield_rate": f"{yield_rate:.1f}%"
    }

@app.get("/reset")
def reset_stats():
    global stats
    stats["total_ok"] = 0
    stats["total_defective"] = 0
    stats["last_status"] = "Reiniciado"
    return {"message": "Contadores reiniciados"}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Panel de Inspección Industrial</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #1e1e2f; color: #fff; margin: 0; padding: 20px; }
            h1 { text-align: center; color: #4db8ff; margin-bottom: 20px; }
            .container { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
            .video-box { background: #2d2d44; padding: 10px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            .video-box img { width: 640px; height: 480px; border-radius: 4px; display: block; }
            .metrics-box { background: #2d2d44; padding: 20px; border-radius: 8px; width: 300px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            .card { background: #3b3b58; padding: 15px; border-radius: 6px; margin-bottom: 15px; text-align: center; }
            .card h3 { margin: 0 0 10px 0; font-size: 14px; color: #aaa; text-transform: uppercase; }
            .card p { margin: 0; font-size: 28px; font-weight: bold; }
            .status-ok { color: #2ecc71; }
            .status-defect { color: #e74c3c; }
            .status-rate { color: #f39c12; }
            button { width: 100%; padding: 12px; background: #e74c3c; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
            button:hover { background: #c0392b; }
        </style>
    </head>
    <body>
        <h1>🔍 Panel de Inspección de Calidad en Tiempo Real</h1>
        <div class="container">
            <div class="video-box">
                <img src="/video_feed" alt="Transmisión en Vivo">
            </div>
            <div class="metrics-box">
                <div class="card">
                    <h3>Estado Actual</h3>
                    <p id="status" class="status-ok">Esperando...</p>
                </div>
                <div class="card">
                    <h3>Piezas OK</h3>
                    <p id="ok-count" class="status-ok">0</p>
                </div>
                <div class="card">
                    <h3>Defectos Detectados</h3>
                    <p id="defective-count" class="status-defect">0</p>
                </div>
                <div class="card">
                    <h3>Tasa de Rendimiento</h3>
                    <p id="yield-rate" class="status-rate">100.0%</p>
                </div>
                <button onclick="resetStats()">Reiniciar Métricas</button>
            </div>
        </div>

        <script>
            async function updateStats() {
                try {
                    const res = await fetch('/stats');
                    const data = await res.json();
                    document.getElementById('ok-count').innerText = data.total_ok;
                    document.getElementById('defective-count').innerText = data.total_defective;
                    document.getElementById('yield-rate').innerText = data.yield_rate;
                    document.getElementById('status').innerText = data.last_status;
                } catch (e) {
                    console.error("Error al obtener estadísticas", e);
                }
            }

            async function resetStats() {
                await fetch('/reset');
                updateStats();
            }

            setInterval(updateStats, 1000);
        </script>
    </body>
    </html>
    """