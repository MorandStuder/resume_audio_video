from outlook_cleaner import get_graph_client


def test_graph_auth():
    """
    Test authentication by fetching a user's profile using application
    permissions.
    """
    client = get_graph_client()
    user_id = input("Entrez l'email d'un utilisateur de votre tenant : ")
    try:
        response = client.get(f'/users/{user_id}')
        if response.status_code == 200:
            user = response.json()
            print("Authentication successful!")
            print(
                f"User: {user.get('displayName')} "
                f"({user.get('userPrincipalName')})"
            )
        else:
            print(
                f"Authentication failed. Status code: {response.status_code}"
            )
            print(response.text)
    except Exception as e:
        print(f"Error during authentication test: {e}")


if __name__ == "__main__":
    test_graph_auth() 