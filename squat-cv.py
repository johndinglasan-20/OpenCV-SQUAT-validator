import cv2
from ultralytics import YOLO

# FIX 1: Usiamo il modello "medium" (m) per una maggiore precisione sui keypoints anatomici
model = YOLO('yolov8l-pose.pt') 

video_path = "IMG_7279.mov" 
cap = cv2.VideoCapture(video_path)

# --- SETUP PER SALVARE IL VIDEO ---
fps = cap.get(cv2.CAP_PROP_FPS)
orig_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
orig_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
altezza = 800
larghezza = int(altezza * (orig_w / orig_h))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("squat_analizzato.mp4", fourcc, fps, (larghezza, altezza))

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_count = 0 

print(f"Inizio elaborazione di {total_frames} frame. Attendi...")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame_count += 1
    if frame_count % 30 == 0:
        print(f"Processato frame {frame_count}/{total_frames}...")

    # Inferenza sulla GPU
    results = model(frame, device=0, verbose=False)

    annotated_frame = results[0].plot()

    # --- LOGICA DI VALIDAZIONE DELLO SQUAT ---
    if results[0].keypoints is not None and len(results[0].keypoints.xy) > 0:
        keypoints = results[0].keypoints.xy[0]
        
        # FIX 2: Prendiamo DIRETTAMENTE E SOLO il lato destro (che è a favore di camera)
        hip_y = float(keypoints[12][1])   # 12 = Anca Destra
        knee_y = float(keypoints[14][1])  # 14 = Ginocchio Destro
        
        if hip_y > 0 and knee_y > 0:
            # VALIDAZIONE: L'anca è sotto il ginocchio? (Ricorda, Y cresce verso il basso)
            parallelo_rotto = hip_y > knee_y
            
            # Imposta i colori (BGR in OpenCV: Verde per Valido, Rosso per Alto)
            colore = (0, 255, 0) if parallelo_rotto else (0, 0, 255)
            
            # 1. Disegna la linea di riferimento orizzontale ESATTAMENTE sul ginocchio destro
            y_linea = int(knee_y)
            cv2.line(annotated_frame, (0, y_linea), (int(orig_w), y_linea), colore, 4)
            
            # 2. Scrivi il verdetto a schermo
            testo = "VALIDO (SOTTO IL PARALLELO)" if parallelo_rotto else "NO LIFT (ALTO)"
            cv2.putText(annotated_frame, testo, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 3, colore, 7)

    # Ridimensiona e salva il frame
    frame_ridimensionato = cv2.resize(annotated_frame, (larghezza, altezza))
    out.write(frame_ridimensionato)

cap.release()
out.release()
print("Elaborazione completata! Controlla 'squat_analizzato.mp4'.")