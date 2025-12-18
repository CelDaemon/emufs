#!/bin/bash
set -ue
script_dir="$(dirname "$0")"
replace_bin="$script_dir/replace.py"

snapshots_dir="$(mktemp -d)"
work_dir="$(mktemp -d)"
trap "rm -rf '$snapshots_dir' '$work_dir'" EXIT

IFS=$'\n' commit_lines=($(git log --grep='Level: .\+' --format='%H%x09%f' emudevz))

git worktree add --detach "$work_dir" emudevz
"$replace_bin" ./save.devz ./save.devz "$work_dir/code" /code
git worktree remove "$work_dir"

for commit in "${commit_lines[@]}"
do
    commit_hash="$(printf "$commit" | cut -f1)"
    snapshot_name="$(printf "$commit" | cut -f2 | tr '[:upper:]' '[:lower:]')"
    git worktree add --detach "$work_dir" "$commit_hash"
    cp -rT "$work_dir/code" "$snapshots_dir/$snapshot_name"
    git worktree remove "$work_dir"
done

"$replace_bin" ./save.devz ./save.devz "$snapshots_dir" /.snapshots
