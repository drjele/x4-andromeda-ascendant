#!/usr/bin/env bash
set -euo pipefail

case "$#:${1:-}" in
    0: | 1:--uninstall) ;;
    *)
        echo "usage: ./install.sh [--uninstall]" >&2
        exit 2
        ;;
esac

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$REPO_ROOT/lib/find_x4.sh"
source "$REPO_ROOT/lib/extension.sh"

GAME_PATH="$(find_x4)" || {
    echo "could not find an X4: Foundations installation - set X4_PATH to point at it" >&2
    exit 1
}
prepare_extension_target
begin_extension_transaction

if [[ "--uninstall" == "${1:-}" ]]; then
    if [[ -d "$TARGET" ]]; then
        mv -- "$TARGET" "$TRANSACTION/previous"
    fi
    TRANSACTION_COMMIT=true
    echo "removed $TARGET"
else
    stage_extension
    TRANSACTION_COMMIT=true
    echo "installed $TARGET"
fi
echo "restart X4 for the change to take effect"
