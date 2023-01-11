#!/usr/bin/env bash
set -o pipefail

local_ref=$1
local_sha=$2
remote_ref=$3
remote_sha=$4
project_path=$5

if [ -z "$local_sha" ] || [ -z "$remote_sha" ] || [ $((16#$local_sha)) -eq 0 ]
then
  echo "Precondition failed: hook won't be executed"
  exit 0
fi

pushd $project_path || exit 1

if [ $((16#$remote_sha)) -ne 0 ]
then
  gitlog_params="$remote_sha..$local_sha"
else
# Remote being created or deleted. For complete information view: https://www.git-scm.com/docs/githooks#_pre_push
# We are going to retrieve the commits only accessible from the current branch (local_ref)
  gitlog_params="$local_ref --not $(git for-each-ref --format='%(refname)' refs/heads/ | grep -v "refs/heads/$local_ref")"
fi
filename="/tmp/tnt-git-hook-commits-$(date +%s)"
git log --pretty="format:%H;%aI;%an <%ae>;%s" $gitlog_params 1> $filename
git_exit=$?

# Do nothing on error, just inform and go ahead with "git push" (i.e. conflicts)
if [ $git_exit -ne 0 ]
then
  echo "Unable to retrieve git log information, will not create evidence on TNT but push continues"
  rm $filename
  popd
  exit 0
fi

REMOTE=$(git ls-remote --get-url | head -1)

python3 -m TNTGitHook --commit-msgs-file $filename --remote $REMOTE
python_exit=$?

if [ $python_exit -ne 0 ]
then
  echo "Error executing python hook"
  exit 1
fi
rm $filename

popd
