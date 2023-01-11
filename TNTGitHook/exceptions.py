
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


class CommitMessagesFileNotFoundError(Exception):
    path: str
    path_write_permissions: bool

    def __init__(self, path: str, path_write_permissions: bool):
        self.path = path
        self.path_write_permissions = path_write_permissions

    def __str__(self):
        return f"Commits messages file not found. File data: path={self.path}, path_write_permissions={self.path_write_permissions}"


class EmptyCommitMessagesFileError(Exception):
    path: str
    path_write_permissions: bool
    file_permissions: str
    file_last_access_time: str
    file_last_modification_time: str
    file_ctime: str

    def __init__(self, path: str, path_write_permissions: bool, file_permissions: str, file_last_access_time: str, file_last_modification_time: str, file_ctime: str):
        self.path = path
        self.path_write_permissions = path_write_permissions
        self.file_permissions = file_permissions
        self.file_last_access_time = file_last_access_time
        self.file_last_modification_time = file_last_modification_time
        self.file_ctime = file_ctime

    def __str__(self):
        return f"File data: path={self.path}, path_write_permissions={self.path_write_permissions}, " \
               f"file_permissions={self.file_permissions}, file_last_access_time={self.file_last_access_time}, " \
               f"file_last_modification_time={self.file_last_modification_time}, file_ctime={self.file_ctime}"
