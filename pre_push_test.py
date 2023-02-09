import os
import unittest

from TNTGitHook.pre_push import PrePush
from TNTGitHook.utils import hook_installation_path


class PrePushTestCase(unittest.TestCase):

    pre_push: PrePush

    def setUp(self) -> None:
        self.pre_push = PrePush()

    def test_it_can_write_the_pre_push(self):
        path_to_write = "./test_pre_push.sh"
        self.pre_push.write_in_file(path_to_write, self.pre_push.__str__())
        self.assertTrue(self.pre_push.is_already_a_pre_push_file(path_to_write))
        os.remove(path_to_write)

    def test_the_pre_push_contains_itself(self):
        path_to_write = "./test_pre_push.sh"
        self.pre_push.write_in_file(path_to_write, self.pre_push.__str__())
        self.assertTrue(self.pre_push.is_pre_push_in_file(path_to_write))
        os.remove(path_to_write)

    def test_the_pre_push_string_is_correct(self):
        self.assertEqual(self.pre_push.__str__(),
                         "#!/bin/bash\n"
                         "set -o pipefail\n"
                         "read local_ref local_sha remote_ref remote_sha\n"
                         f"$HOME/.tnt/hook/bin/tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $(git rev-parse --show-toplevel)")

    def test_the_pre_push_string_is_correct_when_there_are_more_elements(self):
        self.assertTrue(self.pre_push.is_pre_push_correct(
                         "#!/bin/bash\n"
                         "read local_ref local_sha remote_ref remote_sha\n"
                         "npm run test:ci\n"
                         f"$HOME/.tnt/hook/bin/tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $(git rev-parse --show-toplevel)"))

    def test_the_pre_push_is_composed_correctly(self):
        self.assertEqual(self.pre_push.compose_pre_hook("#!/bin/sh\nnpm run test:ci"),
                         "#!/bin/bash\n"
                         "set -o pipefail\n"
                         "read local_ref local_sha remote_ref remote_sha\n"
                         "npm run test:ci\n"
                         f"$HOME/.tnt/hook/bin/tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $(git rev-parse --show-toplevel)")

    def test_old_lines_are_removed(self):
        self.assertListEqual([],
                             self.pre_push.remove_old_script_lines(["read local_ref local_sha remote_ref remote_sha",
                                                                    "# Assumes tnt_git_hook.sh is on PATH",
                                                                    "PROJECT_PATH=$(git rev-parse --show-toplevel)",
                                                                    "set -o pipefail",
                                                                    f"$HOME/.tnt/hook/bin/tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $PROJECT_PATH"]))

        self.assertListEqual(["npm run test:ci"],
                             self.pre_push.remove_old_script_lines(["read local_ref local_sha remote_ref remote_sha",
                                                                    "# Assumes tnt_git_hook.sh is on PATH",
                                                                    "npm run test:ci",
                                                                    "PROJECT_PATH=$(git rev-parse --show-toplevel)",
                                                                    "set -o pipefail",
                                                                    f"$HOME/.tnt/hook/bin/tnt_git_hook $local_ref $local_sha $remote_ref $remote_sha $PROJECT_PATH"]))


if __name__ == '__main__':
    unittest.main()
