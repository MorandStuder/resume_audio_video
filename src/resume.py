import os
from process_gloabl import load_api_key, summarize_transcriptions


def read_transcriptions():
    """Lit les transcriptions depuis le dossier transcriptions"""
    transcriptions_dir = "transcriptions"
    if not os.path.exists(transcriptions_dir):
        print("❌ Le dossier 'transcriptions' n'existe pas!")
        return None
    
    # Lire le fichier de transcription complète s'il existe
    complete_path = os.path.join(transcriptions_dir, "transcription_complete.txt")
    if os.path.exists(complete_path):
        with open(complete_path, "r", encoding="utf-8") as f:
            return [f.read()]
    
    # Sinon, lire tous les fichiers de transcription individuels
    transcriptions = []
    for file in sorted(os.listdir(transcriptions_dir)):
        if file.startswith("transcription_") and file.endswith(".txt"):
            with open(os.path.join(transcriptions_dir, file), "r", encoding="utf-8") as f:
                transcriptions.append(f.read())
    
    return transcriptions


def main():
    # Lire les transcriptions
    transcriptions = read_transcriptions()
    if not transcriptions:
        print("❌ Aucune transcription trouvée!")
        return
    
    try:
        # Générer le résumé en utilisant la fonction de process_gloabl
        summarize_transcriptions(transcriptions)
        
        print("\n✅ Résumé terminé avec succès!")
        print(f"📂 Le résumé se trouve dans: {os.path.abspath('resumes')}")
        
    except Exception as e:
        print(f"\n❌ Une erreur s'est produite: {str(e)}")
    
    input("\nAppuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    main() 