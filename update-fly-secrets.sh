#!/usr/bin/env bash
set -euo pipefail

# update-fly-secrets.sh
# - Cleans a .env-like file
# - Normalizes values for this app
# - Writes a Fly-compatible env file
# - Imports into Fly secrets (apply or stage)

INPUT_FILE=.env.example
OUTPUT_FILE=.env.fly
MODE=apply          # apply | stage | dry-run
DEPLOY_AFTER_STAGE=false

print_usage() {
	cat <<'EOF'
Usage: ./update-fly-secrets.sh [options]

Options:
  -i, --input PATH       Source env file (default: .env.example)
  -o, --output PATH      Output env file to import (default: .env.fly)
      --stage            Stage secrets (no restart) then exit
      --deploy           With --stage, also run 'fly secrets deploy'
      --apply            Import immediately (default)
      --dry-run          Generate output but do not import
  -h, --help             Show this help

Notes:
- Drops comments, blank lines, and empty values
- Strips wrapping quotes in values
- Normalizes PRODUCTION to true/false
- Normalizes CROP_ALIGNMENT to center|left (defaults to center if invalid)
- Removes unused storage keys based on STORAGE_BACKEND (tigris|filesystem)
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
	case "$1" in
		-i|--input)
			INPUT_FILE="$2"; shift 2;;
		-o|--output)
			OUTPUT_FILE="$2"; shift 2;;
		--stage)
			MODE=stage; shift;;
		--deploy)
			DEPLOY_AFTER_STAGE=true; shift;;
		--apply)
			MODE=apply; shift;;
		--dry-run)
			MODE=dry-run; shift;;
		-h|--help)
			print_usage; exit 0;;
		*)
			echo "Unknown option: $1" >&2; print_usage; exit 1;;
	esac
done

# Preconditions
if ! command -v fly >/dev/null 2>&1; then
	echo "Error: 'fly' CLI is not installed or not in PATH." >&2
	echo "Install: https://fly.io/docs/flyctl/install/" >&2
	exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
	echo "Error: input file not found: $INPUT_FILE" >&2
	exit 1
fi

TMP1="$(mktemp)"; TMP2="$(mktemp)"; TMP3="$(mktemp)"
trap 'rm -f "$TMP1" "$TMP2" "$TMP3"' EXIT

# 1) Remove inline comments, full-line comments, and blank lines
#    - Inline comments only when preceded by whitespace:  KEY=VAL    # comment
sed -E 's/[[:space:]]+#.*$//' "$INPUT_FILE" | sed -E '/^\s*#/d;/^\s*$/d' > "$TMP1"

# 2) Strip wrapping quotes from values
awk -F= '
function ltrim(s){ sub(/^[[:space:]]+/, "", s); return s }
function rtrim(s){ sub(/[[:space:]]+$/, "", s); return s }
function trim(s){ return rtrim(ltrim(s)) }
function strip_quotes(s){
	if (s ~ /^".*"$/ || s ~ /^\x27.*\x27$/) { sub(/^"|^\x27/, "", s); sub(/"$|\x27$/, "", s) }
	return s
}
BEGIN { OFS = "=" }
!/=/ { next }
{
	key=$1; key=rtrim(key)
	val=substr($0, index($0, "=")+1); val=trim(val); val=strip_quotes(val)
	if (val=="") next
	print key, val
}
' "$TMP1" > "$TMP2"

# 3) Normalize keys/values and drop unused ones by backend
awk -F= '
function ltrim(s){ sub(/^[[:space:]]+/, "", s); return s }
function rtrim(s){ sub(/[[:space:]]+$/, "", s); return s }
function trim(s){ return rtrim(ltrim(s)) }
BEGIN { OFS = "=" }
!/=/ { next }
{
	key=$1; key=rtrim(key)
	val=substr($0, index($0, "=")+1); val=trim(val)

	# Normalize specific values
	if (key=="PRODUCTION") {
		low=val; for(i=1;i<=length(val);i++){ c=substr(val,i,1); low=tolower(val) }
		if (low=="true" || low=="1" || low=="yes") val="true"; else val="false"
	}
	if (key=="CROP_ALIGNMENT") {
		low=tolower(val)
		if (low!="center" && low!="left") val="center"; else val=low
	}
	pairs[key]=val
	order[++n]=key
}
END{
	backend="tigris"; if ("STORAGE_BACKEND" in pairs) backend=tolower(pairs["STORAGE_BACKEND"])
	for (i=1;i<=n;i++) {
		k=order[i]; v=pairs[k]
		if (backend=="filesystem") {
			if (k ~ /^AWS_/ || k ~ /^TIGRIS_/) continue
		} else if (backend=="tigris") {
			if (k ~ /^FILESYSTEM_/) continue
		}
		print k, v
	}
}
' "$TMP2" > "$TMP3"

mv "$TMP3" "$OUTPUT_FILE"
echo "Generated $OUTPUT_FILE"

case "$MODE" in
	"dry-run")
		echo "--- $OUTPUT_FILE ---"; cat "$OUTPUT_FILE"; echo "(dry-run: not importing)";;
	"stage")
		echo "Staging secrets to Fly from $OUTPUT_FILE ..."
		fly secrets import --stage < "$OUTPUT_FILE"
		if [[ "$DEPLOY_AFTER_STAGE" == true ]]; then
			echo "Deploying staged secrets ..."
			fly secrets deploy
		fi
		;;
	"apply")
		echo "Importing secrets to Fly from $OUTPUT_FILE ..."
		fly secrets import < "$OUTPUT_FILE"
		;;
	*)
		echo "Unknown mode: $MODE" >&2; exit 1;;
esac 