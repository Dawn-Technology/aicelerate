#!/bin/bash
# Footer: ctx · chr · lines │ 5h │ 7d ........ sid: <session id>
# Local only: reads stdin JSON, no network, no file writes.
in=$(cat)
now=${MOCK_NOW:-$(date +%s)}
E=$'\033'; R="${E}[0m"; DIM="${E}[2m"

num()  { [[ $1 =~ ^[0-9]+(\.[0-9]+)?$ ]] && printf '%s' "$1"; }   # validated number or nothing
int()  { local n; n=$(num "$1") || return; printf '%.0f' "$n"; }
jqv()  { echo "$in" | jq -r "$1 // empty" 2>/dev/null; }          # one field per call: no tab-shift bug

seg() { # label used_pct resets_at
  local used reset left rem cd c
  used=$(num "$2"); reset=$(int "$3")
  [ -z "$used" ] || [ -z "$reset" ] && return
  left=$(echo "100 - $used" | bc -l); left=$(int "$(echo "if ($left < 0) 0 else $left" | bc -l)"); [ -z "$left" ] && return
  rem=$(( reset - now )); [ $rem -lt 0 ] && rem=0
  cd=$(printf '%02dd %02dh' $((rem/86400)) $(((rem%86400)/3600)))
  c=32; [ $left -le 40 ] && c=33; [ $left -le 15 ] && c=31
  printf '%s %s[%sm%s%%%s · ⏳%s' "$1" "$E" "$c" "$left" "$R" "$cd"
}
join() { local o=""; for p in "$@"; do [ -n "$p" ] && o="${o:+$o │ }$p"; done; printf '%s' "$o"; }

# session id: letters, digits, - and _ only (no control chars reach the terminal)
sid=$(jqv '.session_id' | tr -cd 'A-Za-z0-9_-')

# ctx: % USED, with hint
ctx=""; cx=$(int "$(jqv '.context_window.used_percentage')")
if [ -n "$cx" ]; then
  cc=32; hint=""
  [ $cx -ge 50 ] && cc=33 hint="wrap up"
  [ $cx -ge 70 ] && cc='38;5;208' hint="no new"
  [ $cx -ge 85 ] && cc=31 hint="finish"
  ctx="ctx ${E}[${cc}m${cx}%${R}${hint:+ ${E}[${cc}m${hint}${R}}"
fi

# chr: cache hit ratio (0-1 -> %), only when reported
chr=""; hr=$(num "$(jqv '.prompt_cache.hit_ratio')")
[ -n "$hr" ] && chr="chr $(int "$(echo "$hr * 100" | bc -l)")%"

# lines changed, only when reported (cost deliberately not shown)
lines=""; la=$(int "$(jqv '.cost.total_lines_added')"); lr=$(int "$(jqv '.cost.total_lines_removed')")
[ -n "$la" ] && [ -n "$lr" ] && lines="${E}[32m+${la}${R}/${E}[31m-${lr}${R}"

w5=$(seg 5h "$(jqv '.rate_limits.five_hour.used_percentage')" "$(jqv '.rate_limits.five_hour.resets_at')")
w7=$(seg 7d "$(jqv '.rate_limits.seven_day.used_percentage')" "$(jqv '.rate_limits.seven_day.resets_at')")

left=$(join "$ctx" "$chr" "$lines" "$w5" "$w7")
right=""; [ -n "$sid" ] && right="sid: $sid"
[ -z "$left$right" ] && exit 0

plain=$(printf '%s' "$left" | sed "s/${E}\\[[0-9;]*m//g")
hg=$(printf '%s' "$plain" | grep -o '⏳' | wc -l)
vis=$(( ${#plain} + hg ))
cols=$(int "${COLUMNS:-0}"); cols=${cols:-0}
pad=$(( cols - 14 - vis - ${#right} ))
if [ -z "$right" ]; then printf '%s\n' "$left"
elif [ $pad -ge 2 ]; then printf '%s%*s%s%s%s\n' "$left" $pad "" "$DIM" "$right" "$R"
else
  [ -n "$left" ] && printf '%s\n' "$left"
  p2=$(( cols - 14 - ${#right} )); [ $p2 -lt 0 ] && p2=0
  printf '%*s%s%s%s\n' $p2 "" "$DIM" "$right" "$R"
fi
