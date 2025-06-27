Sub SupprimerElementsEnvoyesAvecJournal()
    Dim olApp As Outlook.Application
    Dim olNamespace As Outlook.Namespace
    Dim xlApp As Object
    Dim wb As Object
    Dim ws As Object
    Dim logFilePath As String
    Dim suppressionType As String
    Dim minSize As Double, minAge As Long
    Dim sentFolder As Outlook.Folder
    Dim journalFilePath As String
    Dim journalWb As Object
    Dim journalWs As Object
    Dim journalRow As Long
    Dim olMail As Object
    Dim Att As Attachment
    Dim emailDate As Date
    Dim ageInDays As Long
    Dim i As Long

    ' Initialisation de l'application Outlook et accès au dossier des éléments envoyés
    Set olApp = New Outlook.Application
    Set olNamespace = olApp.GetNamespace("MAPI")
    Set sentFolder = olNamespace.GetDefaultFolder(olFolderSentMail)

    ' Chemin du fichier Excel avec les instructions
    logFilePath = Environ("USERPROFILE") & "\Documents\Instructions_Suppression_ElementsEnvoyes.xlsx"

    ' Initialisation de l'application Excel
    On Error Resume Next
    Set xlApp = GetObject(, "Excel.Application")
    If xlApp Is Nothing Then
        Set xlApp = CreateObject("Excel.Application")
    End If
    xlApp.Visible = True
    On Error GoTo 0

    ' Ouvrir le fichier d'instructions, gérer les erreurs si le fichier n'existe pas
    On Error Resume Next
    Set wb = xlApp.Workbooks.Open(logFilePath)
    If wb Is Nothing Then
        MsgBox "Le fichier d'instructions n'existe pas. Veuillez d'abord exécuter le script de création.", vbCritical
        Exit Sub
    End If
    On Error GoTo 0
    Set ws = wb.Sheets(1)

    ' Lire les instructions dans le fichier Excel
    suppressionType = ws.Cells(2, 4).Value
    minSize = ws.Cells(2, 5).Value * 1024 * 1024 ' Conversion Mo -> octets
    minAge = ws.Cells(2, 6).Value

    ' Initialisation du journal Excel
    journalFilePath = Environ("USERPROFILE") & "\Documents\Journal_Suppressions_ElementsEnvoyes.xlsx"
    On Error Resume Next
    Set journalWb = xlApp.Workbooks.Open(journalFilePath)
    If journalWb Is Nothing Then
        Set journalWb = xlApp.Workbooks.Add
        journalWb.SaveAs journalFilePath
    End If
    On Error GoTo 0
    Set journalWs = journalWb.Sheets(1)

    ' Ajouter les en-têtes du journal si la feuille est vide
    If journalWs.Cells(1, 1).Value = "" Then
        journalWs.Cells(1, 1).Value = "Date de Suppression"
        journalWs.Cells(1, 2).Value = "Objet de l'Email"
        journalWs.Cells(1, 3).Value = "Date de l'Email"
        journalWs.Cells(1, 4).Value = "Nom de la Pièce Jointe Supprimée"
        journalWs.Cells(1, 5).Value = "Type de Suppression"
    End If
    journalRow = journalWs.Cells(journalWs.Rows.Count, 1).End(-4162).Row + 1

    ' Parcours des éléments dans le dossier des éléments envoyés avec une boucle For
    For i = sentFolder.Items.Count To 1 Step -1
        Set olMail = sentFolder.Items(i)
        
        ' Vérifier que l'élément est bien un email (MailItem)
        If TypeOf olMail Is Outlook.MailItem Then
            emailDate = olMail.ReceivedTime
            ageInDays = DateDiff("d", emailDate, Now)

            ' Appliquer les critères de suppression
            If suppressionType = "Pièce jointe" Then
                ' Supprimer les pièces jointes selon la taille et l'âge minimum
                For Each Att In olMail.Attachments
                    If Att.Size >= minSize And ageInDays >= minAge Then
                        ' Journaliser avant suppression
                        journalWs.Cells(journalRow, 1).Value = Now
                        journalWs.Cells(journalRow, 2).Value = olMail.Subject
                        journalWs.Cells(journalRow, 3).Value = emailDate
                        journalWs.Cells(journalRow, 4).Value = Att.FileName
                        journalWs.Cells(journalRow, 5).Value = "Pièce jointe"
                        journalRow = journalRow + 1

                        ' Supprimer la pièce jointe et sauvegarder
                        Att.Delete
                        olMail.Save
                    End If
                Next Att
            ElseIf suppressionType = "Email" Then
                ' Supprimer l'email entier si l'âge et la taille sont conformes
                If olMail.Size >= minSize And ageInDays >= minAge Then
                    ' Journaliser avant suppression
                    journalWs.Cells(journalRow, 1).Value = Now
                    journalWs.Cells(journalRow, 2).Value = olMail.Subject
                    journalWs.Cells(journalRow, 3).Value = emailDate
                    journalWs.Cells(journalRow, 4).Value = "Email entier"
                    journalWs.Cells(journalRow, 5).Value = "Email"
                    journalRow = journalRow + 1

                    ' Supprimer l'email
                    olMail.Delete
                End If
            End If
        End If
    Next i

    ' Sauvegarder et fermer le fichier Excel des instructions et du journal
    wb.Save
    wb.Close SaveChanges:=True
    journalWb.Save
    journalWb.Close SaveChanges:=True

    ' Message de confirmation
    MsgBox "Suppression effectuée selon les instructions du fichier Excel.", vbInformation

    ' Libération des objets
    Set olMail = Nothing
    Set journalWs = Nothing
    Set journalWb = Nothing
    Set ws = Nothing
    Set wb = Nothing
    Set xlApp = Nothing
    Set sentFolder = Nothing
    Set olNamespace = Nothing
    Set olApp = Nothing
End Sub
