
class NoCredentialsError(Exception):
    def __str__(self):
        return "No credentials supplied, use 'TNTGitHook --set-credentials' first"


class AuthError(Exception):
    def __str__(self):
        return "Invalid credentials, use 'TNTGitHook --set-credentials' to fix them"


class NetworkError(Exception):
    status: int

    def __init__(self, status: int = 400):
        self.status = status

    def __str__(self):
        # return "TNT not reachable or malfunctioning. Please, check availability."
        return f"TNT not reachable or malfunctioning. Please, check availability. HTTP return code: {self.status}"


class NotFoundError(Exception):
    item: str
    value: str

    def __init__(self, item: str, value: str):
        self.item = item
        self.value = value

    def __str__(self):
        return self.item + " with name \"" + self.value + "\" not found in TNT"


class EmptyCommitMessages(Exception):
    def __str__(self):
        return "Empty commit messages. It may be produced due to a temporary error. Please try again"
