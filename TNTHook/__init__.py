import argparse

from TNTHook.hook import create_activity, Config


def main(argv=None):
    parser = argparse.ArgumentParser(description="TNTHook")
    parser.add_argument('--debug', action='store_const', const=True, default=False)
    parser.add_argument('--commit-msgs', help="Commit messages", required=True)
    parser.add_argument('--prev-commit-date-str', help="Previous commit date", required=False)
    args = parser.parse_args()

    create_activity(Config.config(args.debug), "Empresa 1", "Test Project", "Maquetador", True,
                    commit_msgs=args.commit_msgs)