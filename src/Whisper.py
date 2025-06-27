import os
import whisper

# === PARAMÈTRES ===
input_directory = "segments_audio"  # Dossier où sont les MP3
output_directory = "transcriptions"
model_size = "base"  # Choix du modèle : tiny, base, small, medium, large

# === PRÉPARATION ===
os.makedirs(output_directory, exist_ok=True)
model = whisper.load_model(model_size)

# === TRANSCRIPTION DE TOUS LES FICHIERS MP3 ===
for filename in sorted(os.listdir(input_directory)):
    if filename.endswith(".mp3"):
        audio_path = os.path.join(input_directory, filename)
        result = model.transcribe(audio_path, language="fr")
        
        # Nom de fichier sans extension
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_directory, f"{base_name}.txt")
        
        # Sauvegarde de la transcription
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        
        print(f"✅ Transcription enregistrée : {output_path}")

print("🎯 Toutes les transcriptions sont terminées.")
