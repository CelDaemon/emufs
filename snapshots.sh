#!/bin/sh
set -ue
script_dir="$(dirname "$0")"
replace_bin="$script_dir/replace.py"

snapshots_dir="$(mktemp -d)"
work_dir="$(mktemp -d)"
trap "rm -rf '$snapshots_dir' '$work_dir'" EXIT

git worktree add --detach "$work_dir" emudevz
"$replace_bin" ./save.devz ./save.devz "$work_dir/code" /code
git worktree remove "$work_dir"

git log --grep='Level: .\+' --format='%H' emudevz | while read -r commit_hash
do
    snapshot_name="level-$(git show --format='%b' --no-patch "$commit_hash" | sed -nE 's/.*Level: ([a-z0-9\-]+).*/\1/p')"
    git worktree add --detach "$work_dir" "$commit_hash"
    cp -rT "$work_dir/code" "$snapshots_dir/$snapshot_name"
    git worktree remove "$work_dir"
done

"$replace_bin" ./save.devz ./save.devz "$snapshots_dir" /.snapshots
