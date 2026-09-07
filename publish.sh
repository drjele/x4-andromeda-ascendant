#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$REPO_ROOT/lib/find_x4.sh"

WORKSHOP_ID_FILE="$REPO_ROOT/steam/workshop-id"

die() {
    echo "$*" >&2
    exit 1
}

usage() {
    cat >&2 <<'USAGE'
usage:
  ./publish.sh publish                 first upload of the extension
  ./publish.sh update "what changed"   update the published item
USAGE
    exit 2
}

COMMAND="${1:-}"
case "$COMMAND" in
    publish)
        [[ 1 -eq $# ]] || usage
        [[ -f "$WORKSHOP_ID_FILE" ]] \
            && die "$WORKSHOP_ID_FILE already exists - the item is published, use: ./publish.sh update \"...\""
        ;;
    update)
        [[ 2 -eq $# && -n "${2:-}" ]] || usage
        CHANGENOTE="$2"
        [[ -f "$WORKSHOP_ID_FILE" ]] \
            || die "no $WORKSHOP_ID_FILE - nothing has been published yet, use: ./publish.sh publish"
        ;;
    *) usage ;;
esac

find_workshop_tool() {
    local TOOL_CANDIDATE
    if [[ -n "${X_TOOLS_PATH:-}" ]]; then
        if [[ -f "$X_TOOLS_PATH" ]]; then
            printf '%s\n' "$X_TOOLS_PATH"
            return 0
        fi
        TOOL_CANDIDATE="$X_TOOLS_PATH/WorkshopTool.exe"
        [[ -f "$TOOL_CANDIDATE" ]] || return 1
        printf '%s\n' "$TOOL_CANDIDATE"
        return 0
    fi
    local TOOL_DIRECTORY
    TOOL_DIRECTORY="$(find_in_libraries "X Tools")" || return 1
    TOOL_CANDIDATE="$(find "$TOOL_DIRECTORY" -maxdepth 2 -iname 'WorkshopTool.exe' -print -quit)"
    [[ -n "$TOOL_CANDIDATE" ]] || return 1
    printf '%s\n' "$TOOL_CANDIDATE"
}

find_proton() {
    if [[ -n "${PROTON_PATH:-}" ]]; then
        [[ -x "$PROTON_PATH/proton" ]] || return 1
        printf '%s\n' "$PROTON_PATH"
        return 0
    fi
    local LIBRARY_DIRECTORY PROTON_CANDIDATE=""
    while IFS= read -r LIBRARY_DIRECTORY; do
        local TOOL_DIRECTORY
        for TOOL_DIRECTORY in "$LIBRARY_DIRECTORY"/steamapps/common/Proton*; do
            [[ -x "$TOOL_DIRECTORY/proton" ]] || continue
            PROTON_CANDIDATE="$TOOL_DIRECTORY"
            [[ "$TOOL_DIRECTORY" == *Experimental* ]] && {
                printf '%s\n' "$TOOL_DIRECTORY"
                return 0
            }
        done
    done < <(steam_libraries)
    [[ -n "$PROTON_CANDIDATE" ]] || return 1
    printf '%s\n' "$PROTON_CANDIDATE"
}

steam_root() {
    local LIBRARY_DIRECTORY
    while IFS= read -r LIBRARY_DIRECTORY; do
        printf '%s\n' "$LIBRARY_DIRECTORY"
        return 0
    done < <(steam_libraries)
    return 1
}

win_path() {
    printf 'Z:%s\n' "${1//\//\\}"
}

GAME_PATH="$(find_x4)" || {
    die "could not find an X4: Foundations installation - set X4_PATH to point at it"
}
[[ -d "$GAME_PATH/extensions" ]] || die "no extensions directory at $GAME_PATH/extensions"

TOOL="$(find_workshop_tool)" || {
    die "could not find WorkshopTool.exe - install the X Tools package (steam://install/282160),
or set X_TOOLS_PATH to the directory holding it"
}

EXTENSION_ID="$(extension_id "$REPO_ROOT/extension/content.xml")"
[[ -n "$EXTENSION_ID" ]] || die "could not read the extension id out of extension/content.xml"
STAGE="$GAME_PATH/extensions/$EXTENSION_ID"
[[ -f "$REPO_ROOT/extension/preview.jpg" ]] || die "extension/preview.jpg is missing"

echo "game:  $GAME_PATH"
echo "tool:  $TOOL"
echo "stage: $STAGE"

rm -rf -- "$STAGE"
mkdir -p -- "$STAGE"
cp -r -- "$REPO_ROOT/extension/." "$STAGE/"

if [[ -f "$WORKSHOP_ID_FILE" ]]; then
    WORKSHOP_ID="$(tr -cd '0-9' <"$WORKSHOP_ID_FILE")"
    [[ -n "$WORKSHOP_ID" ]] || die "$WORKSHOP_ID_FILE holds no digits"
    sed -i "s/id=\"$EXTENSION_ID\"/id=\"ws_$WORKSHOP_ID\"/" "$STAGE/content.xml"
    echo "item:  ws_$WORKSHOP_ID"
fi

run_tool() {
    case "$(uname -s)" in
        MINGW* | MSYS* | CYGWIN* | Windows_NT)
            (cd "$(dirname "$TOOL")" && ./"$(basename "$TOOL")" "$@")
            ;;
        *)
            local PROTON_DIRECTORY STEAM_DIRECTORY COMPATIBILITY_DIRECTORY
            PROTON_DIRECTORY="$(find_proton)" \
                || die "could not find Proton - install any Proton version from Steam, or set PROTON_PATH"
            STEAM_DIRECTORY="$(steam_root)"
            COMPATIBILITY_DIRECTORY="$(dirname "$(dirname "$TOOL")")/../compatdata/282160"
            mkdir -p -- "$COMPATIBILITY_DIRECTORY"
            echo "proton: $PROTON_DIRECTORY"
            STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_DIRECTORY" \
                STEAM_COMPAT_DATA_PATH="$(cd "$COMPATIBILITY_DIRECTORY" && pwd)" \
                "$PROTON_DIRECTORY/proton" run "$TOOL" "$@"
            ;;
    esac
}

STAGE_WIN="$(win_path "$STAGE")"
case "$(uname -s)" in
    MINGW* | MSYS* | CYGWIN* | Windows_NT) STAGE_WIN="$STAGE" ;;
esac

if [[ "publish" == "$COMMAND" ]]; then
    run_tool publishx4 -path "$STAGE_WIN" -preview "$STAGE_WIN\\preview.jpg" -buildcat
else
    run_tool update -path "$STAGE_WIN" -buildcat -changenote "$CHANGENOTE"
fi

NEW_ID="$(extension_id "$STAGE/content.xml" | tr -cd '0-9')"
if [[ "publish" == "$COMMAND" ]]; then
    [[ -n "$NEW_ID" ]] || die "the tool did not write a Workshop id into $STAGE/content.xml - upload failed?"
    mkdir -p -- "$(dirname "$WORKSHOP_ID_FILE")"
    printf '%s\n' "$NEW_ID" >"$WORKSHOP_ID_FILE"
    echo
    echo "published as https://steamcommunity.com/sharedfiles/filedetails/?id=$NEW_ID"
    echo "the item is hidden until you open that page, accept the Steam Workshop Legal Agreement"
    echo "and set the visibility to public"
    echo
    echo "commit the new $WORKSHOP_ID_FILE - ./publish.sh update needs it"
fi

"$REPO_ROOT/install.sh" >/dev/null
echo "local install restored to id=$EXTENSION_ID"
