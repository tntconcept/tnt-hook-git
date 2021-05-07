#!/bin/bash
set -o pipefail

read local_ref local_sha remote_ref remote_sha

if [ -n "$local_sha" ] && [ -n "$remote_sha" ] && [ $((16#$local_sha)) -ne 0 ]
then
  CMD='git log --pretty="format:%H;%aI;%an <%ae>;%s"'
  if [ $((16#$remote_sha)) -ne 0 ]
  then
    CMD="$CMD $remote_sha..$local_sha"
  else
# Remote being created or deleted. For complete information view: https://www.git-scm.com/docs/githooks#_pre_push
# When retrieving the commit with sha as above the order is altered, so we need to reverse it.
# We are retrieving the complete commit list, so in order to avoid TNT activity description overflow we will limit the number retrieved
    CMD="$CMD --reverse"
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

