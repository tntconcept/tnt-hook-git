import hashlib
from pathlib import Path

from TNTGitHook import hook
from TNTGitHook.hook import write_hook_script, Config, setup_config, removes_old_hook_file
from TNTGitHook.pre_push import PrePush


def is_update_needed():
    hook_file = Path(f"{str(Path.home())}/.tnt/hook/bin/tnt_git_hook")
    if not hook_file.is_file():
        print("Hook not in the path")
        return True
    else:
        with open(hook_file) as open_hook_file:
            current_sha1 = hashlib.sha1(open_hook_file.read().encode('utf8')).hexdigest()
            if current_sha1 != hook.get_hook_sha1():
                print("Different hook versions")
                return True
    return False


def write_hook():
    print("Writing hook")
    write_hook_script()
    print("Hook written")


def setup(config: Config, organization: str, project: str, role: str):
    removes_old_hook_file()
    write_hook_script()
    write_pre_push_script()
    setup_config(config, organization, project, role)


def write_pre_push_script():
    pre_push = PrePush()
    pre_push.setup()

