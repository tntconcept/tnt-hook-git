#!/bin/bash

read local_ref local_sha remote_ref remote_sha

if [ -n "$local_sha" ] && [ -n "$remote_sha" ]
then
  if [ $((16#$remote_sha)) -eq 0 ]
  then
    MSGS=`git log --pretty="format:%H;%aI;%an <%ae>;%s"`
  else
    MSGS=`git log --pretty="format:%H;%aI;%an <%ae>;%s" $remote_sha..$local_sha`
  fi
  REMOTE=`git ls-remote --get-url | head -1`

  # Assumes TNTGitHook is on PATH
  TNTGitHook --commit-msgs "$MSGS" --remote $REMOTE
fi

