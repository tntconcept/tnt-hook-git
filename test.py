import unittest
from TNTGitHook import hook


class HookTestCase(unittest.TestCase):
    def test_generated_info_order_should_be_from_recent_to_older(self):
        commits = hook.read_commit_msgs("new_branch_commits")
        info = hook.generate_info(commits)
        print(info[0])
        self.assertRegex(
            info[0],
            expected_regex=get_regex(),
            msg="Expected commit order doesn't comply"
        )
        # self.assertEqual(True, False)


def get_regex() -> str:
    header = r'(^###Autocreated evidence###\n\(DO NOT DELETE\)\n){1}'
    sha = r'([\da-f]{40}\n)'
    formatted_time = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}\n)'
    commiter = r'(.+<.+@.+>\n)'
    commit_message = r'(.+)'
    record_separator = r'(\n-{5})?'
    return f'{header}({sha}{formatted_time}{commiter}{commit_message}{record_separator})+'


if __name__ == '__main__':
    unittest.main()
