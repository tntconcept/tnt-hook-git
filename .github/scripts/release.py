#!/usr/bin/env python3
import json
import subprocess


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
    """Return a copy of `version_number` with the minor number incremented."""
    major, minor, patch = version_number.split(".")
    return f"{major}.{int(minor) + 1}.{patch}"


def replace_version_number(last_version_number: str, new_version_number: str):
    file_content = generate_setup_file_content_with_new_version(last_version_number, new_version_number)
    write_new_setup_file(file_content)


def write_new_setup_file(file_content: str):
    file_input = open("setup.py", "wt")
    file_input.write(file_content)
    file_input.close()


def generate_setup_file_content_with_new_version(last_version_number: str, new_version_number: str) -> str:
    file_input = open("setup.py", "rt")
    file_content = file_input.read()
    file_content = file_content.replace(last_version_number, new_version_number)
    file_input.close()
    return file_content


def create_new_minor_release():
    """Create a new minor release on GitHub."""
    try:
        last_version_number = get_last_version()
    except subprocess.CalledProcessError as err:
        print(err.stderr.decode("utf8"))
        if err.stderr.decode("utf8").startswith("release not found"):
            # The project doesn't have any releases yet.
            new_version_number = "0.1.0"
            print(f"Release not found. Starting with {new_version_number}")
        else:
            raise
    else:
        new_version_number = bump_minor_number(last_version_number)
        if new_version_number != "0.1.0":
            replace_version_number(last_version_number, new_version_number)

    subprocess.run(
        ["gh", "release", "create", "--generate-notes", new_version_number],
        check=True,
    )


if __name__ == "__main__":
    create_new_minor_release()
