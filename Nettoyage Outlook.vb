Sub DeleteLargeAttachments()

    'Définissez les paramètres de la recherche
    Dim strSearch As String
    Dim strFolder As String
    Dim dtDate As Date

    strSearch = "hasattachments:yes"
    strFolder = "Boîte de réception"
    dtDate = DateAdd("d", -2000, Now)

    'Exécutez la recherche
    Set objFolder = Outlook.Application.Session.GetDefaultFolder(strFolder)
    Set objItems = objFolder.Items

    countDeleted = 0

    'Parcourez les messages
    For Each objItem In objItems

        'Vérifiez la taille de la pièce jointe
        Dim strAttachment As String
        Dim intSize As Long

        strAttachment = objItem.Attachments(1).FileName
        intSize = objItem.Attachments(1).Size

        'Supprimez la pièce jointe si elle est volumineuse et si le message a été reçu avant la date spécifiée
        If intSize > 1000000 And objItem.ReceivedTime < dtDate Then
            objItem.Attachments(1).Delete
            countDeleted = countDeleted + 1
        End If

        Next
' Notification du nombre d'emails supprimés
    MsgBox countDeleted & " emails supprimés plus vieux que " & dtDate, vbInformation

        ' Libération des objets
        Set objItem = Nothing

End Sub


    Sub NettoyerBoiteMail()
        Dim olApp As Outlook.Application
        Dim olNamespace As Outlook.Namespace
        Dim olFolder As Outlook.Folder
        Dim olItems As Outlook.Items
        Dim olMail As Object
        Dim delDate As Date
        Dim countDeleted As Integer
    
        ' Initialisation de l'application Outlook et des dossiers
        Set olApp = New Outlook.Application
        Set olNamespace = olApp.GetNamespace("MAPI")
        Set olFolder = olNamespace.GetDefaultFolder(olFolderInbox) ' Changer si besoin pour un autre dossier
    
        ' Définir la date limite pour suppression (par exemple, 30 jours)
        delDate = Now - 30
        countDeleted = 0
    
        ' Parcours de tous les emails dans le dossier spécifié
        For Each olMail In olFolder.Items
            If TypeName(olMail) = "MailItem" Then
                ' Vérifie si l'email est plus vieux que la date limite
                If olMail.ReceivedTime < delDate Then
                    olMail.Delete
                    countDeleted = countDeleted + 1
                End If
            End If
        Next olMail
    
        ' Notification du nombre d'emails supprimés
        MsgBox countDeleted & " emails supprimés plus vieux que " & delDate, vbInformation
    
        ' Libération des objets
        Set olMail = Nothing
        Set olItems = Nothing
        Set olFolder = Nothing
        Set olNamespace = Nothing
        Set olApp = Nothing
    End Sub
    