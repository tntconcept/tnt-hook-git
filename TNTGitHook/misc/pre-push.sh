#!/bin/bash
set -o pipefail

read local_ref local_sha remote_ref remote_sha

if [ -n "$local_sha" ] && [ -n "$remote_sha" ] && [ $((16#$local_sha)) -ne 0 ]
then
  CMD='git log --pretty="format:%H;%aI;%an <%ae>;%s"'
  if [ $((16#$remote_sha)) -ne 0 ]
  then
    CMD="$CMD $remote_sha..$local_sha"
  fi
  CMD="$CMD 2> /dev/null"
  MSGS=`eval $CMD`

  # Do nothing on error, just inform and go ahead with "git push" (i.e. conflicts)
  if [ $? -ne 0 ]
  then
    echo "Unable to retrieve git log information, will not create evidence on TNT"
    exit 0
  fi

  REMOTE=`git ls-remote --get-url | head -1`

  # Assumes TNTGitHook is on PATH
  TNTGitHook --commit-msgs "$MSGS" --remote $REMOTE
fi

