import os

# === PARAMÈTRES ===
input_directory = "transcriptions"       # Dossier contenant les .txt
output_file = "verbatim_complet.txt"     # Fichier final
segment_duration_min = 15                # Pour horodatage approximatif

# === COMBINAISON & MISE EN FORME ===
with open(output_file, "w", encoding="utf-8") as out_file:
    for idx, filename in enumerate(sorted(os.listdir(input_directory))):
        if filename.endswith(".txt"):
            segment_number = idx + 1
            start_min = segment_duration_min * (segment_number - 1)
            end_min = start_min + segment_duration_min

            out_file.write(f"\n=== Segment {segment_number:02d} — de {start_min:02d} à {end_min:02d} min ===\n\n")

            with open(os.path.join(input_directory, filename), "r", encoding="utf-8") as f:
                text = f.read().strip()

                # Mise en forme simple : sauts de ligne après chaque point
                formatted = text.replace(". ", ".\n")
                
                # (Optionnel) Préparer pour identification manuelle des intervenants :
                # formatted = formatted.replace("\n", "\nIntervenant : ")

                out_file.write(formatted)
                out_file.write("\n\n")

print(f"📄 Verbatim structuré généré dans : {output_file}")
