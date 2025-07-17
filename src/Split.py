import os
import numpy as np
import librosa
import soundfile as sf
import argparse
from moviepy.video.io.VideoFileClip import VideoFileClip

def split_audio(input_path: str, segment_duration_min: int = 30, output_directory: str = "segments_audio") -> list[str]:
    """
    Découpe un fichier audio (mp3, wav, etc.) ou vidéo (mp4, avi, etc.) en segments MP3 de durée fixe.
    - Si le fichier est une vidéo, l'audio est extrait automatiquement.
    - Si le fichier est un audio, il est traité directement.
    Les segments sont exportés dans le dossier de sortie.
    """
    os.makedirs(output_directory, exist_ok=True)
    file_ext = os.path.splitext(input_path)[1].lower()
    audio_path = input_path

    # Si c'est une vidéo, extraire l'audio temporairement
    if file_ext in [".mp4", ".avi", ".mkv", ".mov"]:
        print(f"Extraction de l'audio depuis la vidéo {input_path}...")
        with VideoFileClip(input_path) as video:
            audio_path = os.path.join(output_directory, "_temp_audio.wav")
            video.audio.write_audiofile(audio_path, codec="pcm_s16le")
    else:
        print(f"Traitement direct du fichier audio {input_path}...")

    # Charger l'audio
    print("Chargement de l'audio...")
    audio, sr = librosa.load(audio_path, sr=None, mono=True)
    total_duration_sec = audio.shape[0] / sr
    segment_duration_sec = segment_duration_min * 60
    num_segments = int(np.ceil(total_duration_sec / segment_duration_sec))

    print(f"Découpage en {num_segments} segments de {segment_duration_min} minutes...")
    segments_paths = []
    for i in range(num_segments):
        start_sec = i * segment_duration_sec
        end_sec = min((i + 1) * segment_duration_sec, total_duration_sec)
        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        segment = audio[start_sample:end_sample]
        output_path = os.path.join(output_directory, f"segment_{i+1:02d}.mp3")
        sf.write(output_path, segment, sr, format='MP3')
        segments_paths.append(output_path)
        print(f"✅ Segment {i+1} exporté : {output_path}")

    # Nettoyage du fichier temporaire
    if audio_path != input_path and os.path.exists(audio_path):
        os.remove(audio_path)

    print(f"\n✅ Tous les segments ont été exportés dans {output_directory}!")
    return segments_paths


def main():
    parser = argparse.ArgumentParser(description="Découpe un fichier vidéo/audio en segments MP3.")
    parser.add_argument("input_path", help="Chemin du fichier vidéo ou audio à découper")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Durée des segments en minutes (défaut: 30)")
    parser.add_argument("-o", "--output", default="segments_audio", help="Dossier de sortie (défaut: segments_audio)")
    args = parser.parse_args()
    split_audio(args.input_path, args.duration, args.output)

if __name__ == "__main__":
    main()
