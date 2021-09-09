from getpass import getpass

import keyring
from keyring.errors import PasswordDeleteError

NAME: str = "TNTGitHook"


def ask():
    # Store the user as single value in keychain to avoid multiple ask for password
    username = input("User: ")
    password = getpass()
    keyring.set_password(f"com.autentia.{NAME}", "credentials", f"{username}:{password}")
    # TODO: remove code below when every user has migrated
    try:
        keyring.delete_password(f"com.autentia.{NAME}", "username")
        keyring.delete_password(f"com.autentia.{NAME}", "password")
    except PasswordDeleteError:
        # We have already deleted old values, no true error so we can continue
        pass
