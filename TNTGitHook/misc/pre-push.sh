#!/bin/bash
set -o pipefail

read local_ref local_sha remote_ref remote_sha

# Assumes tnt_git_hook.sh is on PATH
tnt_git_hook "$local_ref" "$local_sha" "$remote_ref" "$remote_sha"
