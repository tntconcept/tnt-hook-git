import copy
import os
import stat
import sys
from pathlib import Path
from typing import List


class PrePush:
    path: str = ".git/hooks/pre-push"
    shebang_symbol: str = '#!'
    shebang: str = '#!/bin/bash'
    pipefail: str = 'set -o pipefail'
    readline: str = 'read local_ref local_sha remote_ref remote_sha'
    tnt_call: str = 'tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $(git rev-parse --show-toplevel)'
    old_script_to_delete: List[str] = ['set -o pipefail', 'PROJECT_PATH', 'tnt_git_hook',
                                       'read local_ref local_sha remote_ref remote_sha']

    def write(self) -> None:
        self.write_in_file(self.path, self.__str__())

    def write_in_file(self, path: str, hook: str) -> None:
        try:
            with open(path, "w") as f:
                f.write(hook)
                st = os.stat(path)
                os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except FileNotFoundError:
            print("Unable to setup hook. Is this a git repository?\nMaybe you're not at the root folder.")
        except Exception as ex:
            print(ex)

    def is_already_a_pre_push(self) -> bool:
        return self.is_already_a_pre_push_file(self.path)

    def is_already_a_pre_push_file(self, path: str) -> bool:
        try:
            hook_file = Path(self.path)
            if hook_file.is_file():
                return True
            return False
        except FileNotFoundError:
            print("Unable to setup hook. Is this a git repository?\nMaybe you're not at the root folder.")
        except Exception as ex:
            print(ex)

    def is_pre_push_in_default_file(self) -> bool:
        return self.is_pre_push_in_file(self.path)

    def is_pre_push_in_file(self, path: str) -> bool:
        if self.is_already_a_pre_push():
            hook_content = Path(path).read_text()
            return self.is_pre_push_correct(hook_content)
        return False

    def is_pre_push_correct(self, current_hook: str) -> bool:
        return self.is_shebang_in_place(current_hook) and self.is_readline_in_place(current_hook) \
               and self.is_tnt_call_in_place(current_hook)

    def is_shebang_in_place(self, current_hook: str) -> bool:
        return self.shebang in current_hook

    def is_readline_in_place(self, current_hook: str) -> bool:
        return self.readline in current_hook

    def is_tnt_call_in_place(self, current_hook: str) -> bool:
        return self.tnt_call in current_hook

    def is_shebang_symbol(self, current_hook: str) -> bool:
        return self.tnt_call in current_hook

    def compose_pre_hook(self, current_hook: str) -> str:
        lines_in_hook = current_hook.split("\n")
        if self.shebang_symbol in lines_in_hook[0]:
            lines_in_hook.pop(0)
        given_hook = "\n".join(self.remove_old_script_lines(lines_in_hook))
        return f"{self.shebang}\n{self.pipefail}\n{self.readline}\n{given_hook}\n{self.tnt_call}"

    def read_hook(self) -> str:
        return Path(self.path).read_text()

    def write_hook(self, hook: str) -> None:
        with open(self.path, "w") as f:
            f.write(hook)

    def remove_old_script_lines(self, lines_in_hook: List[str]) -> List[str]:
        result = copy.deepcopy(lines_in_hook)
        for position, line in enumerate(lines_in_hook):
            for item_to_delete in self.old_script_to_delete:
                if item_to_delete in line:
                    result.remove(line)
                    break
        return result

    def setup(self):
        if self.is_already_a_pre_push():
            print("There is already a pre push file\n")
            if self.is_pre_push_in_default_file():
                print("Pre push already in file, nothing to do\n")
            else:
                current_hook = self.read_hook()
                print("=== Current hook ===\n")
                print(current_hook)
                print("== New hook ==\n")
                new_hook = self.compose_pre_hook(current_hook)
                print(new_hook)
                want_write = input("Want to write it? y/n: ")
                if want_write.lower() == 'y':
                    self.write_hook(new_hook)
                else:
                    sys.exit('Cancelled by the user')
        else:
            self.write()

    def __str__(self):
        return f"{self.shebang}\n{self.pipefail}\n{self.readline}\n{self.tnt_call}"
