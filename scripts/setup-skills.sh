#!/bin/bash
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
# setup-skills.sh — Sync SKILLS/ into Claude Code and Codex CLI discovery paths
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: setup-skills.sh [--root DIR] [--skills DIR] [--mirror DEST] [--strict-mirror]

Options:
  --root DIR    Directory that should receive .claude/ and .codex/. Defaults to
                the current git root when available, otherwise the script's
                directory.
  --skills DIR  Explicit path to the SKILLS directory. Defaults to auto-detect.
  --mirror DEST Mirror skills to an additional rsync destination (local or
                remote path like host:/path). Can be repeated.
  --strict-mirror
                Exit non-zero if any --mirror sync fails.
  -h, --help    Show this help text.
USAGE
}

resolve_path() {
    local input="$1"
    if [ ! -d "$input" ]; then
        echo "ERROR: Directory not found — $input" >&2
        exit 1
    fi
    (cd "$input" && pwd)
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT_DIR="$(pwd)"
PARENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ROOT=""
SKILLS_OVERRIDE=""
STRICT_MIRROR=0
declare -a MIRROR_TARGETS

while [ $# -gt 0 ]; do
    case "$1" in
        --root)
            [ $# -ge 2 ] || { echo "ERROR: --root requires a directory" >&2; usage; exit 1; }
            TARGET_ROOT="$(resolve_path "$2")"
            shift 2
            ;;
        --skills)
            [ $# -ge 2 ] || { echo "ERROR: --skills requires a directory" >&2; usage; exit 1; }
            SKILLS_OVERRIDE="$(resolve_path "$2")"
            shift 2
            ;;
        --mirror)
            [ $# -ge 2 ] || { echo "ERROR: --mirror requires a destination" >&2; usage; exit 1; }
            MIRROR_TARGETS+=("$2")
            shift 2
            ;;
        --strict-mirror)
            STRICT_MIRROR=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option — $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [ -z "$TARGET_ROOT" ]; then
    if git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
        TARGET_ROOT="$git_root"
    else
        TARGET_ROOT="$SCRIPT_DIR"
    fi
fi

if [ -z "$SKILLS_OVERRIDE" ]; then
    CANDIDATES=(
        "$TARGET_ROOT/SKILLS"
        "$TARGET_ROOT/prompts/SKILLS"
        "$SCRIPT_DIR/SKILLS"
        "$PARENT_DIR/SKILLS"
        "$PARENT_DIR/prompts/SKILLS"
        "$CURRENT_DIR/SKILLS"
        "$CURRENT_DIR/prompts/SKILLS"
        "$HOME/.codex/skills"
        "$HOME/.claude/skills"
    )
    for candidate in "${CANDIDATES[@]}"; do
        [ -d "$candidate" ] || continue
        SKILLS_OVERRIDE="$candidate"
        break
    done
fi

if [ -z "$SKILLS_OVERRIDE" ]; then
    echo "ERROR: SKILLS/ directory not found." >&2
    echo "       Provide one via --skills or ensure SKILLS/ exists in the repo root." >&2
    exit 1
fi

SKILLS_DIR="$(resolve_path "$SKILLS_OVERRIDE")"

log_skills() {
    local target_dir="$1"
    local found=0
    shopt -s nullglob 2>/dev/null || true
    for dir in "$target_dir"/*/; do
        [ -d "$dir" ] || continue
        found=1
        skill_name="$(basename "$dir")"
        if [ -f "$dir/SKILL.md" ]; then
            printf "    - %s\n" "$skill_name"
        else
            printf "    - %s (missing SKILL.md)\n" "$skill_name"
        fi
    done
    shopt -u nullglob 2>/dev/null || true
    if [ "$found" -eq 0 ]; then
        echo "    (no skills found)"
    fi
}

ensure_skill_manifest() {
    local skill_dir="$1"
    local skill_name="$2"
    local manifest="$skill_dir/SKILL.md"

    if [ ! -f "$manifest" ]; then
        cat >"$manifest" <<EOF
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
# SKILL: $skill_name

## Purpose
Describe the responsibilities and workflow for the "$skill_name" role.

## Usage
- List instructions that Codex or Claude should follow when this skill is invoked.
- Replace this placeholder text with real guidance.
EOF
    fi
}

prepare_skills_tree() {
    local root_dir="$1"
    shopt -s nullglob 2>/dev/null || true
    for skill_path in "$root_dir"/*/; do
        [ -d "$skill_path" ] || continue
        skill_basename="$(basename "$skill_path")"
        ensure_skill_manifest "$skill_path" "$skill_basename"
    done
    shopt -u nullglob 2>/dev/null || true
}

copy_skills() {
    local dest="$1"
    rm -rf "$dest"
    cp -R "$SKILLS_DIR" "$dest"
    prepare_skills_tree "$dest"
}

sync_skills_dir() {
    local target_root="$1"
    local dest="$target_root/skills"

    mkdir -p "$target_root"

    if [ -d "$dest" ]; then
        if diff -qr "$SKILLS_DIR" "$dest" >/dev/null 2>&1; then
            echo "✓ $dest already up to date"
        else
            copy_skills "$dest"
            echo "✓ $dest refreshed from $SKILLS_DIR"
        fi
    else
        copy_skills "$dest"
        echo "✓ $dest created from $SKILLS_DIR"
    fi

    echo "  Skills in $dest:"
    log_skills "$dest"
    echo ""
}

prepare_skills_tree "$SKILLS_DIR"
cd "$TARGET_ROOT"

declare -a skills_buffer

sync_skills_dir .claude
sync_skills_dir .codex

mirror_skills_dir() {
    local dest="$1"

    if rsync -av --delete "$SKILLS_DIR"/ "$dest" >/dev/null 2>&1; then
        echo "✓ mirror refreshed at $dest"
        return 0
    fi

    echo "WARN: mirror failed for $dest" >&2
    return 1
}

mirror_failures=0
for mirror_dest in "${MIRROR_TARGETS[@]}"; do
    mirror_skills_dir "$mirror_dest" || mirror_failures=$((mirror_failures + 1))
done

echo "Skills available at source ($SKILLS_DIR):"
log_skills "$SKILLS_DIR"
echo ""

if [ "$STRICT_MIRROR" -eq 1 ] && [ "$mirror_failures" -gt 0 ]; then
    exit 1
fi
