# 🔍 Sistema de Inspección de Calidad (ESP32-CAM + YOLOv8 + FastAPI)

Este proyecto es un prototipo funcional de un **Sistema de Inspección de Calidad Automatizado en Tiempo Real** para la clasificación de piezas (OK / Defectuosa). El sistema utiliza un microcontrolador ESP32 para la captura de imágenes y con un backend que ejecuta un modelo entrenado para una auditoría automatizada.

---

## 🚀 Características Principales

* **Transmisión de Video en Tiempo Real:** Captura de video vía HTTP Stream desde una tarjeta ESP32-CAM.
* **Inferencia de IA (YOLOv8):** Detección y clasificación instantánea de piezas buenas (`cross_ok`) y defectuosas (`cross_bad`).
* **Lógica de Antirrebote (Debounce Logic):** Algoritmo de filtrado por estados que exige un umbral de fotogramas limpios para prevenir registros e imágenes duplicadas por cada pieza.
* **Captura Automática de Evidencia (Scrap Logging):** Almacenamiento automático de capturas de piezas defectuosas en el directorio `/scrap` con marca de tiempo.
* **Dashboard Web Interactivo:** Interfaz gráfica industrial en FastAPI con actualización periódica de:
  * Conteo total de piezas OK.
  * Conteo de Defectos.
  * **Tasa de Rendimiento (Yield Rate %)** calculada dinámicamente.
  * Botón de reinicio de métricas por turno.

---

## 🛠️ Tecnologías Utilizadas

### Hardware
* **ESP32-CAM** (Módulo de cámara OV2640 con configuración C++ en Arduino IDE).

### Software & Backend
* **Python 3.10+**
* **FastAPI / Uvicorn** (Servidor web asíncrono y streaming multipart).
* **OpenCV** (Procesamiento y decodificación de fotogramas).
* **Ultralytics YOLOv8** (Modelo de detección de objetos entrenado con dataset personalizado y etiquetado en ROBOFLOW).

---

## 📁 Estructura del Proyecto

```text
├── scrap/                  # Carpeta de guardado automático de las piezas defectuosas
├── main.py                 # Servidor FastAPI, pipeline OpenCV y Dashboard HTML
├── best.pt                 # Modelo YOLOv8 entrenado
├── .gitignore              # Archivos excluidos del control de versiones
├── requirements.txt        # Dependencias 
└── README.md               # Documentación del proyecto
```

## ⚙️ Inicio Rápido

1. **Instalar dependencias:**
   `pip install -r requirements.txt`

2. **Configurar la IP:**
   Crear un archivo `.env` con la IP de tu cámara: `ESP32_IP=192.168.1.200`

3. **Ejecutar:**
   `uvicorn main:app --reload`
