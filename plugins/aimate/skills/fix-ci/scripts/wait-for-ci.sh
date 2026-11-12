#!/usr/bin/env bash
# Wait for the CI of one PR/MR to finish and print one JSON verdict.
#
#   wait-for-ci.sh --provider github|gitlab --repo REPO --pr N --sha SHA
#                  [--host HOST] [--after-id PIPELINE_ID]
#                  [--timeout SECONDS] [--appear-timeout SECONDS]
#                  [--interval SECONDS] [--settle SECONDS]
#
# REPO is OWNER/REPO (GitHub, HOST/OWNER/REPO for Enterprise) or the project
# path (GitLab). --host is for self-hosted GitLab only.
#
# stdout is a single JSON object:
#   {"state": green|red|timeout|no-ci|head-moved|closed|error,
#    "head": "<sha>", "pipeline_id": <gitlab only>, "detail": "...",
#    "checks": [{"name","status","link","run_id","job_id"}]}
# status is pass|fail|cancel|pending|skipped; anything the provider reports that is
# not recognised counts as pending, so an unknown state can never read as green.
# "error" means the provider could not be read five times in a row.
# Exit code is 0 whenever a verdict was printed, 2 for bad usage or a missing tool.
#
# On GitLab a job that never ran in an already finished pipeline (for example one
# behind a failed stage) counts as skipped, so it cannot keep the wait open.
#
# A verdict of green or red is only printed after every check has finished and
# the same result has been seen on two polls in a row, so a pipeline that is
# still registering its jobs right after a push is not mistaken for finished.
set -uo pipefail

provider="" repo="" pr="" sha="" host="" after_id=0
timeout=2700 appear_timeout=300 interval=20 settle=0

die() { echo "wait-for-ci: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in --*) [ $# -ge 2 ] || die "$1 needs a value" ;; esac
  case "$1" in
    --provider) provider=${2:-}; shift 2 ;;
    --repo) repo=${2:-}; shift 2 ;;
    --pr) pr=${2:-}; shift 2 ;;
    --sha) sha=${2:-}; shift 2 ;;
    --host) host=${2:-}; shift 2 ;;
    --after-id) after_id=${2:-0}; shift 2 ;;
    --timeout) timeout=${2:-}; shift 2 ;;
    --appear-timeout) appear_timeout=${2:-}; shift 2 ;;
    --interval) interval=${2:-}; shift 2 ;;
    --settle) settle=${2:-}; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$provider" ] && [ -n "$repo" ] && [ -n "$pr" ] && [ -n "$sha" ] || die "--provider, --repo, --pr and --sha are required"
case "$provider" in github) tool=gh ;; gitlab) tool=glab ;; *) die "--provider must be github or gitlab" ;; esac
command -v "$tool" >/dev/null || die "$tool is not installed"
command -v jq >/dev/null || die "jq is not installed"
for n in "$pr" "$after_id" "$timeout" "$appear_timeout" "$interval" "$settle"; do
  case "$n" in ''|*[!0-9]*) die "numeric argument expected, got '$n'" ;; esac
done
case "$sha" in *[!0-9a-fA-F]*|'') die "--sha must be a hexadecimal commit id" ;; esac
[ "${#sha}" -ge 40 ] || die "--sha must be the full commit id, not an abbreviation"

emit() { # state head pipeline_id detail checks_json
  jq -n --arg state "$1" --arg head "$2" --arg pid "${3:-}" --arg detail "${4:-}" \
    --argjson checks "${5:-[]}" \
    '{state:$state, head:$head, detail:$detail, checks:$checks}
     + (if $pid != "" then {pipeline_id: ($pid|tonumber)} else {} end)'
}

# Each fetch prints "open|closed<US>head<US>pipeline_id<US>checks_json" (US is the
# unit separator, so empty fields survive) and
# returns non-zero when the provider could not be read.
fetch_github() {
  local view checks open head errf
  view=$(gh pr view "$pr" -R "$repo" --json headRefOid,state 2>/dev/null) || return 1
  open=$(jq -r 'if .state == "OPEN" then "open" else "closed" end' <<<"$view")
  head=$(jq -r '.headRefOid' <<<"$view")
  # gh exits non-zero while checks are pending or failing, but still prints JSON.
  # With no JSON it either has no checks to report or could not read them; only the
  # first is "no checks yet". Anything else (rate limit, expired login) is a read failure.
  errf=$(mktemp) || return 1
  checks=$(gh pr checks "$pr" -R "$repo" --json name,bucket,link 2>"$errf") || true
  if ! jq -e 'type == "array"' <<<"$checks" >/dev/null 2>&1; then
    if grep -qi 'no checks reported' "$errf"; then checks='[]'; else rm -f "$errf"; return 1; fi
  fi
  rm -f "$errf"
  checks=$(jq -c '[.[] | {
      name,
      status: (
        if .bucket == "pass" then "pass"
        elif .bucket == "fail" then "fail"
        elif .bucket == "cancel" then "cancel"
        elif .bucket == "skipping" then "skipped"
        else "pending" end),
      link,
      run_id: (((.link // "") | capture("/runs/(?<r>[0-9]+)") | .r) // null),
      job_id: (((.link // "") | capture("/job/(?<j>[0-9]+)") | .j) // null)
    }]' <<<"$checks" 2>/dev/null) || checks='[]'
  printf '%s\037%s\037\037%s\n' "$open" "$head" "$checks"
}

glab_api() {
  if [ -n "$host" ]; then glab api --hostname "$host" "$@"; else glab api "$@"; fi
}

fetch_gitlab() {
  local enc mr open head pid pstatus pweb psha pref jobs bridges checks
  enc=$(jq -rn --arg p "$repo" '$p | @uri')
  mr=$(glab_api "projects/$enc/merge_requests/$pr" 2>/dev/null) || return 1
  open=$(jq -r 'if .state == "opened" then "open" else "closed" end' <<<"$mr")
  head=$(jq -r '.sha // ""' <<<"$mr")
  pid=$(jq -r '.head_pipeline.id // 0' <<<"$mr")
  psha=$(jq -r '.head_pipeline.sha // ""' <<<"$mr")
  pref=$(jq -r '.head_pipeline.ref // ""' <<<"$mr")
  # Without --after-id the pipeline must belong to the commit we are waiting for;
  # otherwise right after a push the old head pipeline would be read as the new one.
  # A merged-results pipeline carries a merge commit, so it is matched by its ref.
  if [ "$pid" -le "$after_id" ] ||
     { [ "$after_id" -eq 0 ] && [ "$psha" != "$sha" ] && ! [[ "$pref" =~ ^refs/merge-requests/[0-9]+/merge$ ]]; }; then
    printf '%s\037%s\037\037[]\n' "$open" "$head"
    return 0
  fi
  pstatus=$(jq -r '.head_pipeline.status' <<<"$mr")
  pweb=$(jq -r '.head_pipeline.web_url // ""' <<<"$mr")
  jobs=$(glab_api --paginate "projects/$enc/pipelines/$pid/jobs?per_page=100" 2>/dev/null \
    | jq -s 'add // [] | map(. + {kind: "job"})') || return 1
  bridges=$(glab_api --paginate "projects/$enc/pipelines/$pid/bridges?per_page=100" 2>/dev/null \
    | jq -s 'add // [] | map(. + {kind: "bridge"})') || return 1
  jobs=$(jq -c -n --argjson a "$jobs" --argjson b "$bridges" '$a + $b')
  checks=$(jq -c --arg pstatus "$pstatus" --arg pweb "$pweb" '
      [.[] | {
        name: (.stage + " / " + (if .kind == "bridge" then "trigger " else "" end) + .name),
        status: (
          if .status == "success" then "pass"
          elif .status == "failed" then (if .allow_failure then "pass" else "fail" end)
          elif .status == "canceled" then "cancel"
          elif (.status == "skipped" or .status == "manual") then "skipped"
          elif (["failed","canceled","success","skipped"] | index($pstatus)) then "skipped"
          else "pending" end),
        link: (.downstream_pipeline.web_url // .web_url),
        run_id: null,
        job_id: (if .kind == "job" then (.id | tostring) else null end)
      }] as $c
      | if ($pstatus == "failed" and ([$c[] | select(.status == "fail")] | length) == 0)
        then $c + [{name: "pipeline", status: "fail", link: $pweb, run_id: null, job_id: null}]
        elif (["created","waiting_for_resource","preparing","pending","running","scheduled"] | index($pstatus))
             and ([$c[] | select(.status == "pending")] | length) == 0
        then $c + [{name: "pipeline", status: "pending", link: $pweb, run_id: null, job_id: null}]
        else $c end' <<<"$jobs" 2>/dev/null) || checks='[]'
  printf '%s\037%s\037%s\037%s\n' "$open" "$head" "$pid" "$checks"
}

[ "$settle" -gt 0 ] && sleep "$settle"

start=$(date +%s)
last_verdict="" last_checks='[]' last_head="" last_pid="" read_failures=0
while :; do
  now=$(date +%s)
  elapsed=$((now - start))

  if line=$(fetch_"$provider"); then
    read_failures=0
    IFS=$'\037' read -r open head pid checks <<<"$line"
    last_head=$head last_pid=$pid last_checks=$checks

    if [ "$open" = closed ]; then
      emit closed "$head" "$pid" "The PR/MR is no longer open." "$checks"; exit 0
    fi

    verdict=""
    if [ "$head" != "$sha" ]; then
      [ "$elapsed" -ge "$appear_timeout" ] && { emit head-moved "$head" "$pid" "The PR/MR head is not $sha." "$checks"; exit 0; }
    elif [ "$(jq 'length' <<<"$checks")" -eq 0 ]; then
      [ "$elapsed" -ge "$appear_timeout" ] && { emit no-ci "$head" "$pid" "No checks appeared within ${appear_timeout}s." "[]"; exit 0; }
    elif jq -e 'any(.[]; .status == "pending")' <<<"$checks" >/dev/null; then
      verdict=pending
    elif jq -e 'any(.[]; .status == "fail" or .status == "cancel")' <<<"$checks" >/dev/null; then
      verdict=red
    else
      verdict=green
    fi

    if [ "$verdict" = red ] || [ "$verdict" = green ]; then
      sig="$verdict:$(jq -c '[.[] | [.name, .status]] | sort' <<<"$checks")"
      if [ "$sig" = "$last_verdict" ]; then
        emit "$verdict" "$head" "$pid" "" "$checks"; exit 0
      fi
      last_verdict=$sig
    else
      last_verdict=""
    fi
  else
    read_failures=$((read_failures + 1))
    if [ "$read_failures" -ge 5 ]; then
      emit error "$last_head" "$last_pid" "The provider could not be read $read_failures times in a row (expired login, no access, or the API is down)." "$last_checks"; exit 0
    fi
  fi

  if [ "$elapsed" -ge "$timeout" ]; then
    emit timeout "$last_head" "$last_pid" "CI had not finished after ${timeout}s." "$last_checks"; exit 0
  fi
  sleep "$interval"
done
