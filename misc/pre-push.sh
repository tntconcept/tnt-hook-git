#!/bin/bash

read local_ref local_sha remote_ref remote_sha

if [ -n "$local_sha" ] && [ -n "$remote_sha" ]
then
  MSGS=`git log --pretty="format:%H;%s;%aI" $remote_sha..$local_sha`
  PREV_DATE=`git log -1 --pretty="format:%aI" $remote_sha`

  # Assumes TNTHook is on PATH
  TNTHook --commit-msgs "$MSGS" --prev-commit-date-str "$PREV_DATE"
fi

