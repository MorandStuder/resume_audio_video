import os
import tkinter as tk
from tkinter import filedialog
import whisper
import json
from pathlib import Path
from openai import OpenAI
from Split import split_audio  # Import du module commun
from moviepy.video.io.VideoFileClip import VideoFileClip  # Pour compatibilité moviepy 2.x


def get_media_path():
    """Ouvre une fenêtre de sélection de fichier vidéo ou audio"""
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Sélectionnez votre fichier vidéo ou audio",
        filetypes=[
            ("Fichiers audio", "*.mp3 *.wav *.ogg *.flac"),
            ("Fichiers vidéo", "*.mp4 *.avi *.mkv *.mov"),
            ("Tous les fichiers", "*.*"),
        ],
        # initialdir=os.path.expanduser("~")
        initialdir="C:/Users/moran/OneDrive/Documents/Audacity",
    )

    if file_path and os.path.exists(file_path):
        return file_path
        print(file_path)
    return None


def split_audio_legacy(input_path, segment_duration_min=30):
    """Ancienne fonction, redirigée vers le module commun split_audio."""
    return split_audio(input_path, segment_duration_min, output_directory="segments_audio")


def transcribe_segments(segments_paths):
    """Transcrit les segments audio avec Whisper"""
    print("\n=== ÉTAPE 2: TRANSCRIPTION ===")

    output_directory = "transcriptions"
    os.makedirs(output_directory, exist_ok=True)

    model = whisper.load_model("base")
    transcriptions = []

    for i, audio_path in enumerate(segments_paths, 1):
        print(f"Transcription du segment {i}...")
        result = model.transcribe(audio_path, language="fr")

        # Sauvegarder la transcription individuelle
        output_path = os.path.join(output_directory, f"transcription_{i:02d}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])

        transcriptions.append(result["text"])
        print(f"✅ Segment {i} transcrit")

    # Sauvegarder toutes les transcriptions dans un seul fichier
    full_transcript_path = os.path.join(output_directory, "transcription_complete.txt")
    with open(full_transcript_path, "w", encoding="utf-8") as f:
        for i, text in enumerate(transcriptions, 1):
            f.write(f"\n{'='*50}\n")
            f.write(f"SEGMENT {i}\n")
            f.write(f"{'='*50}\n\n")
            f.write(text)
            f.write("\n\n")

    print(f"✅ Transcription complète sauvegardée: {full_transcript_path}")

    return transcriptions


def load_api_key():
    """Charge la clé API depuis le fichier config ou la demande à l'utilisateur"""
    config_file = Path("config.json")

    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)
            api_key = config.get("OPENAI_API_KEY", "")
            if api_key:
                return api_key

    # Si pas de clé, demander à l'utilisateur
    api_key = input("Entrez votre clé API OpenAI: ").strip()

    # Sauvegarder la clé pour la prochaine fois
    with open(config_file, "w") as f:
        json.dump({"OPENAI_API_KEY": api_key}, f)

    return api_key


def summarize_transcriptions(transcriptions):
    """Résume les transcriptions avec GPT"""
    print("\n=== ÉTAPE 3: RÉSUMÉ ===")

    # Charger la clé API
    client = OpenAI(api_key=load_api_key())

    output_directory = "resumes"
    os.makedirs(output_directory, exist_ok=True)

    # Concaténer toutes les transcriptions
    full_text = "\n\n".join(transcriptions)

    print("Création du résumé global...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un assistant qui met en forme des transcriptions "
                    "de vidéos ou de réunions."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Met en forme cette transcription en français en gardant "
                    "le maximum d'informations, sous la forme d'un texte "
                    "structuré, avec des titres et des sous-titres. "
                    "Organise le contenu de manière claire et logique, "
                    "en mettant en évidence les points importants et les "
                    "éventuelles décisions prises.\n\n"
                    f"{full_text}"
                ),
            },
        ],
    )

    global_summary = response.choices[0].message.content

    # Sauvegarder le résumé global
    with open(
        os.path.join(output_directory, "resume_global.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(global_summary)

    print(f"✅ Résumé global sauvegardé dans: " f"{os.path.abspath(output_directory)}")

    return global_summary


def main():
    print("=== TRAITEMENT MÉDIA ===")

    # Étape 1: Sélection et découpage
    print("\nSélectionnez votre fichier vidéo ou audio...")
    input_path = get_media_path()
    if not input_path:
        print("❌ Aucun fichier sélectionné.")
        return

    try:
        # Découpage audio
        segments_paths = split_audio_legacy(input_path)

        # Transcription
        transcriptions = transcribe_segments(segments_paths)

        # Résumé
        summarize_transcriptions(transcriptions)

        print("\n✅ Traitement terminé avec succès!")
        print("📂 Vous trouverez les fichiers dans les dossiers:")
        print(f"   - Audio: {os.path.abspath('segments_audio')}")
        print(f"   - Transcriptions: {os.path.abspath('transcriptions')}")
        print(f"   - Résumés: {os.path.abspath('resumes')}")

    except Exception as e:
        print(f"\n❌ Une erreur s'est produite: {str(e)}")

    input("\nAppuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    main()
