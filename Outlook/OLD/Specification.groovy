Je veux faire un programme Python permettant d’accéder à une boîte mail Outlook 365, de lister les dossiers et les emails et d’exécuter des actions de nettoyage (suppression de pièces jointes ou d’emails) en fonction d’un fichier Excel de configuration.

Développer un programme Python qui :
	• Se connecte à une boîte Outlook 365.
	• Scanne les emails de tous les dossiers 
	• Génère un fichier Excel contenant une vue d'ensemble des emails et les actions à effetuer 
	Nom du dossier	Nombre d'emails		Taille totale (Go)		Suppression email ou pièce jointe uniquement	Seuil Taille PJ (Mo)	Seuil Âge (années)
	• 3 dernières colonnes à remplir manuellement - Permet de configurer des actions de nettoyage (suppression de pièces jointes ou de mails) via Excel.
	• Si "Action" = "Pièce jointe" et pièce jointe > taille seuil et email > âge seuil → supprimer la pièce jointe.
	• Si "Action" = "Email" et taille > seuil et âge > seuil → supprimer le mail.
	
	• Applique ces instructions avec journalisation dans un fichier de log.
