#!/usr/bin/env python3
import json
import subprocess
import os


def get_last_version() -> str:
    """Return the version number of the last release."""
    json_string = (
        subprocess.run(
            ["gh", "release", "view", "--json", "tagName"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        .stdout.decode("utf8")
        .strip()
    )

    return json.loads(json_string)["tagName"]


def bump_minor_number(version_number: str) -> str:
    """Return a copy of `version_number` with the patch number incremented."""
    major, minor, patch = version_number.split(".")
    return f"{major}.{int(minor) + 1}.{patch}"


def replace_version_number(last_version_number, new_version_number):
    # input file
    print(os.listdir("../../"))
    print(os.listdir())
    fin = open("../../setup.py", "rt")

    # output file to write the result to
    out_mode = open("../../setup.py", "wt")
    # for each line in the input file
    for line in fin:
        # read replace the string and write to output file
        out_mode.write(line.replace(last_version_number, new_version_number))
    # close input and output files
    fin.close()
    out_mode.close()


def create_new_patch_release():
    """Create a new patch release on GitHub."""
    try:
        last_version_number = get_last_version()
    except subprocess.CalledProcessError as err:
        print(err.stderr.decode("utf8"))
        if err.stderr.decode("utf8").startswith("release not found"):
            # The project doesn't have any releases yet.
            new_version_number = "0.0.1"
            print(f"Release not found. Starting with {new_version_number}")
        else:
            raise
    else:
        new_version_number = bump_minor_number(last_version_number)
        if new_version_number != "0.0.1":
            replace_version_number(last_version_number, new_version_number)

    subprocess.run(
        ["gh", "release", "create", "--generate-notes", new_version_number],
        check=True,
    )


if __name__ == "__main__":
    create_new_patch_release()
