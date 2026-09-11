extension_id() {
    python3 - "$1" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET

try:
    root = ET.parse(sys.argv[1]).getroot()
    value = root.get("id", "")
    if root.tag != "content" or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is None:
        raise ValueError("invalid extension id")
    print(value)
except (OSError, ET.ParseError, ValueError) as error:
    print(error, file=sys.stderr)
    sys.exit(1)
PY
}

prepare_extension_target() {
    GAME_PATH="$(cd -- "$GAME_PATH" && pwd -P)" || return 1
    [[ -d "$GAME_PATH/extensions" && ! -L "$GAME_PATH/extensions" ]] || {
        echo "expected a real extensions directory inside $GAME_PATH" >&2
        return 1
    }
    EXTENSION_ID="$(extension_id "$REPO_ROOT/extension/content.xml")" || return 1
    TARGET="$GAME_PATH/extensions/$EXTENSION_ID"
    [[ ! -L "$TARGET" && (! -e "$TARGET" || -d "$TARGET") ]] || {
        echo "refusing non-directory or symlink target: $TARGET" >&2
        return 1
    }
    [[ "$TARGET" != "$(cd "$REPO_ROOT/extension" && pwd -P)" ]] || {
        echo "installation target is the source extension" >&2
        return 1
    }
}

cleanup_extension_transaction() {
    local STATUS=$? RESTORED=true
    trap - EXIT INT TERM
    if [[ "$TRANSACTION_COMMIT" != true ]]; then
        if [[ "$TRANSACTION_REPLACING" == true ]]; then
            rm -rf -- "$TARGET" || RESTORED=false
        fi
        if [[ -d "$TRANSACTION/previous" && "$RESTORED" == true ]]; then
            mv -- "$TRANSACTION/previous" "$TARGET" || RESTORED=false
        fi
    fi
    if [[ "$RESTORED" == true ]]; then
        rm -rf -- "$TRANSACTION" || STATUS=1
    else
        echo "restore failed; previous installation retained at $TRANSACTION/previous" >&2
        STATUS=1
    fi
    rmdir -- "$TRANSACTION_LOCK" || STATUS=1
    exit "$STATUS"
}

begin_extension_transaction() {
    TRANSACTION_LOCK="$GAME_PATH/.$EXTENSION_ID.lock"
    mkdir -- "$TRANSACTION_LOCK" || {
        echo "another install or publish may be active: $TRANSACTION_LOCK" >&2
        return 1
    }
    TRANSACTION="$(mktemp -d "$GAME_PATH/.$EXTENSION_ID.XXXXXX")" || {
        rmdir -- "$TRANSACTION_LOCK"
        return 1
    }
    TRANSACTION_COMMIT=false
    TRANSACTION_REPLACING=false
    trap cleanup_extension_transaction EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

stage_extension() {
    mkdir -- "$TRANSACTION/new"
    cp -a -- "$REPO_ROOT/extension/." "$TRANSACTION/new/"
    [[ "$(extension_id "$TRANSACTION/new/content.xml")" == "$EXTENSION_ID" ]]
    if [[ -d "$TARGET" ]]; then
        mv -- "$TARGET" "$TRANSACTION/previous"
    fi
    TRANSACTION_REPLACING=true
    mv -- "$TRANSACTION/new" "$TARGET"
}
