#!/usr/bin/env python3
"""Condense one session's transcript into a small digest, locally (no network, no model).
usage: python3 -I scan_history.py <session-id> [--max-chars N]   (default 12000)
Prints: the user's own messages, plus the first 300 chars of each assistant final reply per turn.
Skips tool results, system reminders and command output. Newest content wins when truncating.
"""
import glob, json, os, re, sys
sid = sys.argv[1]
cap = int(sys.argv[sys.argv.index('--max-chars') + 1]) if '--max-chars' in sys.argv else 12000
paths = glob.glob(os.path.expanduser(f'~/.claude/projects/*/{sid}.jsonl'))
if not paths: sys.exit('no transcript for that session id')
def text_of(c):
    if isinstance(c, str): return c
    return '\n'.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text')
out = []
for l in open(paths[0]):
    try: d = json.loads(l)
    except Exception: continue
    m = d.get('message')
    if not isinstance(m, dict): continue
    t = text_of(m.get('content', ''))
    t = re.sub(r'<(system-reminder|local-command-[a-z]+|command-[a-z]+|task-notification)[^>]*>.*?</\1>', '', t, flags=re.S).strip()
    if not t or t.startswith(('This session is being continued', '[SYSTEM', 'Caveat')): continue
    if d.get('type') == 'user' and not d.get('toolUseResult'): out.append('USER: ' + t[:600])
    elif d.get('type') == 'assistant': out.append('CLAUDE: ' + t[:300])
digest = '\n'.join(out)
if len(digest) > cap: digest = '[older part cut]\n' + digest[-cap:]
print(digest)
print(f'\n[digest {len(digest)} chars, about {len(digest)//4} tokens]', file=sys.stderr)
