
class NoCredentialsError(Exception):
    def __str__(self):
        return "No credentials supplied, use 'TNTHook --set-credentials' first"


class AuthError(Exception):
    def __str__(self):
        return "Invalid credentials, use 'TNTHook --set-credentials' to fix them"


class NotFoundError(Exception):
    item: str
    value: str

    def __init__(self, item: str, value: str):
        self.item = item
        self.value = value

    def __str__(self):
        return self.item + " with name \"" + self.value + "\" not found in TNT"
