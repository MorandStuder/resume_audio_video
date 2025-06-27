from pydub import AudioSegment
import os
import tkinter as tk
from tkinter import filedialog


def get_video_path():
    """Ouvre une fenêtre de sélection de fichier vidéo"""
    # Cacher la fenêtre principale de tkinter
    root = tk.Tk()
    root.withdraw()

    # Ouvrir le sélecteur de fichier
    file_path = filedialog.askopenfilename(
        title="Sélectionnez votre fichier vidéo",
        filetypes=[
            ("Fichiers vidéo", "*.mp4 *.avi *.mkv *.mov"),
            ("Tous les fichiers", "*.*")
        ],
        initialdir=os.path.expanduser("~")  # Démarre dans le dossier utilisateur
    )

    # Vérifier si un fichier a été sélectionné
    if file_path and os.path.exists(file_path):
        return file_path
    else:
        print("❌ Erreur : Aucun fichier sélectionné.")
        return None


# === PARAMÈTRES ===
print("=== CONFIGURATION ===")
print("\nOuverture de la fenêtre de sélection...")
input_video_path = get_video_path()

if input_video_path:
    output_directory = "segments_audio"
    segment_duration_min = 30  # Durée en minutes

    # === CRÉATION DU DOSSIER DE SORTIE ===
    os.makedirs(output_directory, exist_ok=True)

    try:
        # Charger le fichier audio
        print("\nChargement de la vidéo...")
        audio = AudioSegment.from_file(input_video_path, format="mp4")
        
        # Calculer la durée des segments
        segment_duration_ms = segment_duration_min * 60 * 1000  # En millisecondes
        total_duration = len(audio)
        num_segments = (
            total_duration + segment_duration_ms - 1
        ) // segment_duration_ms

        print(
            f"\nDécoupage de la vidéo en {num_segments} segments "
            f"de {segment_duration_min} minutes..."
        )

        # Découper et exporter les segments
        for i in range(num_segments):
            start = i * segment_duration_ms
            end = min((i + 1) * segment_duration_ms, total_duration)
            
            segment = audio[start:end]
            output_path = os.path.join(
                output_directory,
                f"segment_{i+1:02d}.mp3"
            )
            
            print(f"\nExport du segment {i+1}...")
            segment.export(
                output_path,
                format="mp3",
                parameters=["-q:a", "0"]  # Meilleure qualité MP3
            )
            print(f"✅ Segment {i+1} exporté : {output_path}")

        print("\n✅ Tous les segments ont été exportés avec succès!")
        print(
            f"📂 Vous les trouverez dans le dossier : "
            f"{os.path.abspath(output_directory)}"
        )

    except FileNotFoundError:
        print(
            f"\n❌ Erreur : Le fichier vidéo n'a pas été trouvé : "
            f"{input_video_path}"
        )
    except Exception as e:
        print(f"\n❌ Une erreur s'est produite : {str(e)}")

input("\nAppuyez sur Entrée pour fermer...")
