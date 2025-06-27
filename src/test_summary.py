import os
import json
from pathlib import Path
from openai import OpenAI
import anthropic
from transformers import pipeline
from mistralai.client import MistralClient
from google.cloud import aiplatform
from vertexai.language_models import TextGenerationModel


def load_api_key():
    """Charge la clé API depuis le fichier config"""
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


def get_model_choice():
    """Permet à l'utilisateur de choisir le modèle"""
    print("\nChoisissez le modèle à utiliser:")
    print("1. GPT-3.5-turbo (OpenAI - payant mais rapide)")
    print("2. Claude-2 (Anthropic - alternative à GPT)")
    print("3. BART (Hugging Face - gratuit, local)")
    print("4. GPT-3.5-turbo-16k (OpenAI - plus de contexte)")
    print("5. Mistral Large (Français, très performant)")
    print("6. Google PaLM 2 (Via Vertex AI)")
    
    choice = input("\nVotre choix (1-6): ").strip()
    return choice


def summarize_with_openai(text, client, model="gpt-3.5-turbo"):
    """Résumé avec OpenAI"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant qui résume des transcriptions."
            },
            {
                "role": "user",
                "content": f"Résume ce texte en français de manière concise et structurée:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content


def summarize_with_claude(text, client):
    """Résumé avec Claude"""
    response = client.messages.create(
        model="claude-2",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"Résume ce texte en français de manière concise et structurée:\n\n{text}"
            }
        ]
    )
    return response.content


def summarize_with_bart(text):
    """Résumé avec BART"""
    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        tokenizer="facebook/bart-large-cnn"
    )
    
    # BART a une limite de tokens, donc on découpe si nécessaire
    max_chunk_length = 1024
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    
    return " ".join(summaries)


def summarize_with_mistral(text, api_key):
    """Résumé avec Mistral AI"""
    client = MistralClient(api_key=api_key)
    
    response = client.chat(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant qui résume des transcriptions."
            },
            {
                "role": "user",
                "content": "Résume ce texte en français de manière structurée:"
                          f"\n\n{text}"
            }
        ]
    )
    return response.messages[0].content


def summarize_with_google(text):
    """Résumé avec Google PaLM"""
    aiplatform.init(project="votre-projet")
    model = TextGenerationModel.from_pretrained("text-bison@001")
    
    prompt = (
        "Résume le texte suivant en français de manière structurée:"
        f"\n\n{text}"
    )
    
    response = model.predict(prompt, temperature=0.2)
    return response.text


def load_mistral_key():
    """Charge la clé API Mistral"""
    config_file = Path("config.json")
    
    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)
            api_key = config.get("MISTRAL_API_KEY", "")
            if api_key:
                return api_key
    
    api_key = input("Entrez votre clé API Mistral: ").strip()
    
    # Mettre à jour le fichier config
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)
    config["MISTRAL_API_KEY"] = api_key
    with open(config_file, "w") as f:
        json.dump(config, f)
    
    return api_key


def test_summary():
    """Test la partie résumé avec différents modèles"""
    print("=== TEST DU RÉSUMÉ ===")
    
    # Vérifier le fichier de transcription
    transcript_path = "transcriptions/transcription_complete.txt"
    if not os.path.exists(transcript_path):
        print("❌ Erreur: Fichier transcription_complete.txt non trouvé")
        return
    
    # Choix du modèle
    choice = get_model_choice()
    
    # Configuration selon le choix
    if choice in ['1', '4']:
        client = OpenAI(api_key=load_api_key())
        model = "gpt-4o"
        summarize_func = lambda text: summarize_with_openai(text, client, model)
    elif choice == '2':
        client = anthropic.Anthropic(api_key=load_anthropic_key())
        summarize_func = lambda text: summarize_with_claude(text, client)
    elif choice == '5':
        api_key = load_mistral_key()
        summarize_func = lambda text: summarize_with_mistral(text, api_key)
    elif choice == '6':
        summarize_func = summarize_with_google
    else:
        summarize_func = summarize_with_bart
    
    # Lire la transcription
    with open(transcript_path, "r", encoding="utf-8") as f:
        full_text = f.read()
    
    # Diviser en segments
    segments = full_text.split("="*50)
    segments = [s.strip() for s in segments if s.strip()]
    
    # Créer le dossier des résumés
    output_directory = "resumes"
    os.makedirs(output_directory, exist_ok=True)
    
    try:
        # Résumer chaque segment
        summaries = []
        for i, text in enumerate(segments, 1):
            print(f"\nRésumé du segment {i}...")
            
            summary = summarize_func(text)
            
            output_path = os.path.join(output_directory, f"resume_{i:02d}.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)
            
            summaries.append(summary)
            print(f"✅ Segment {i} résumé")
        
        # Résumé global
        print("\nCréation du résumé global...")
        all_text = "\n\n".join(summaries)
        global_summary = summarize_func(all_text)
        
        with open(os.path.join(output_directory, "resume_global.txt"), "w", 
                  encoding="utf-8") as f:
            f.write(global_summary)
        
        print("\n✅ Traitement terminé!")
        print(f"📂 Résumés sauvegardés dans: {os.path.abspath(output_directory)}")
        
    except Exception as e:
        print(f"\n❌ Une erreur s'est produite: {str(e)}")
    
    input("\nAppuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    test_summary() 