#!/bin/bash
set -o pipefail

local_ref=$1
local_sha=$2
remote_ref=$3
remote_sha=$4

if [ -n "$local_sha" ] && [ -n "$remote_sha" ] && [ $((16#$local_sha)) -ne 0 ]
then
  CMD='git log --pretty="format:%H;%aI;%an <%ae>;%s"'
  if [ $((16#$remote_sha)) -ne 0 ]
  then
    CMD="$CMD $remote_sha..$local_sha"
  else
# Remote being created or deleted. For complete information view: https://www.git-scm.com/docs/githooks#_pre_push
# We are going to retrieve the commits only accessible from the current branch (local_ref)
    CMD="$CMD $local_ref --not $(git for-each-ref --format='%(refname)' refs/heads/ | grep -v "refs/heads/$local_ref")"
  fi
  CMD="$CMD 2> /dev/null"
  FILENAME="/tmp/tnt-git-hook-commits-$(date +%s)"
  eval $CMD > $FILENAME

  # Do nothing on error, just inform and go ahead with "git push" (i.e. conflicts)
  if [ $? -ne 0 ]
  then
    echo "Unable to retrieve git log information, will not create evidence on TNT but push continues"
    exit 0
  fi

  REMOTE=$(git ls-remote --get-url | head -1)

  # Assumes TNTGitHook is on PATH
  TNTGitHook --commit-msgs-file $FILENAME --remote $REMOTE
  rm $FILENAME
fi

