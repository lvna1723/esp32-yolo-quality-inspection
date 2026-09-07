import cv2
import os
from dotenv import load_dotenv
from ultralytics import YOLO

# Cargar variables de entorno 
load_dotenv()

# construir la URL
esp32_ip = os.getenv("ESP32_IP")
print(f"Intentando conectar a la IP: {esp32_ip}")
esp32_url = f"http://{esp32_ip}:81/stream"

# Cargar el modelo
model = YOLO('best.pt')

# Conectar al flujo de video
cap = cv2.VideoCapture(esp32_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print(f"Error: No se pudo conectar a la ESP32-CAM en {esp32_url}")
    exit()
    
print("Conectado a la ESP32-CAM. Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al leer el fotograma.")
        break
    
    results = model.predict(source=frame, conf=0.5, verbose=False)
    annotated_frame = results[0].plot()
    
    cv2.imshow("Inspeccion - YOLOv8", annotated_frame)
    
    if cv2.waitKey(1) & 0xFF ==ord('q'):
        break

cap.release()
cv2.destroyAllWindows()