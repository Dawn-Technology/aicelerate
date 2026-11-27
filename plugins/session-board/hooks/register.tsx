import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const PANE = 'session-board'
// A repo has a board when it has .claude/board.md, or a TASKS.md carrying the <!-- board --> marker.
// Board data stays in the repo it belongs to; this mod holds no project content.
const MARKER = '<!-- board -->'
const NOBOARD = '\u0000noboard '
const CANDIDATES = ['.claude/board.md', 'TASKS.md']
const text = atom({ plugin: 'session-board', key: 'text' } as const, '', { shape: 'text-1' })

type Found = { name: string; src: string }

const sessionBoardPath = async ($: any): Promise<string | undefined> => {
  try {
    const home: string | undefined = await $.env.get('HOME')
    const id: string = await $.session.id()
    return home && id ? `${home}/.claude/boards/${id}.md` : undefined
  } catch {
    return undefined
  }
}

// Order: this session's own board, then a repo board in the session's directory or root.
const findBoard = async ($: any): Promise<{ found?: Found; diag: string }> => {
  const tried: string[] = []
  const own = await sessionBoardPath($)
  if (own) {
    try {
      return { found: { name: own, src: await $.fs.read(own) }, diag: '' }
    } catch {
      tried.push(`session board ${own}: not created yet`)
    }
  } else {
    tried.push('session id or HOME unknown')
  }
  const dirs: string[] = []
  for (const get of [() => $.session.cwd(), () => $.session.root()]) {
    try {
      const d: string = await get()
      if (d && !dirs.includes(d)) dirs.push(d)
    } catch {
      /* skip */
    }
  }
  for (const dir of dirs) {
    for (const name of CANDIDATES) {
      try {
        const src: string = await $.fs.read(`${dir}/${name}`)
        if (name !== 'TASKS.md' || src.includes(MARKER)) return { found: { name: `${dir}/${name}`, src }, diag: '' }
        tried.push(`${dir}/${name}: no ${MARKER} marker`)
      } catch {
        tried.push(`${dir}/${name}: not found`)
      }
    }
  }
  return { diag: `looked in: ${tried.join(' | ')}` }
}

type Row = { kind: 'h' | 'todo' | 'doing' | 'done' | 'note'; label: string }

const parse = (src: string): Row[] =>
  src.split('\n').flatMap((line): Row[] => {
    const h = /^#{1,3}\s+(.*)/.exec(line)
    if (h) return [{ kind: 'h', label: h[1] ?? '' }]
    const t = /^\s*[-*]\s+\[([ xX~])\]\s+(.*)/.exec(line)
    if (t) {
      const mark = t[1]
      return [{ kind: mark === ' ' ? 'todo' : mark === '~' ? 'doing' : 'done', label: t[2] ?? '' }]
    }
    return line.trim() === '' ? [] : [{ kind: 'note', label: line.trim() }]
  })

const load = async ($: any) => {
  const { found, diag } = await findBoard($)
  const src = found ? found.src : `${NOBOARD}${diag}`
  await update($, text, old => (old === src ? old : src))
  if (!found) {
    void $.ui.status(undefined)
    return
  }
  const r = parse(src).filter(x => x.kind === 'todo' || x.kind === 'doing' || x.kind === 'done')
  const d = r.filter(x => x.kind === 'done').length
  void $.ui.status(r.length === 0 ? undefined : `Board ${Math.round((d / r.length) * 100)}% (${d}/${r.length})`)
}

// session.start does not fire when the plugin is loaded mid-session (/reload-plugins), so /session-board starts polling too.
let polling = false
const startPolling = async ($: any) => {
  await load($)
  if (polling) return
  polling = true
  $.clock.every(2000, () => {
    void load($)
  })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'session-board', description: 'Open this session\'s task board pane' })
    await startPolling($)
    // Resuming (same session id) brings the board back: open the pane when this session already has items.
    try {
      const own = await sessionBoardPath($)
      if (own) {
        const saved: string = await $.fs.read(own)
        if (/^\s*[-*]\s+\[[ xX~]\]/m.test(saved)) void $.ui.open({ id: PANE, title: 'Board' })
      }
    } catch {
      /* no board for this session: stay closed */
    }
    return next(e)
  })

  on('command.run', { command: 'session-board' }, async ($, e) => {
    const own = await sessionBoardPath($)
    let hasOwn = false
    if (own) {
      try {
        await $.fs.read(own)
        hasOwn = true
      } catch {
        hasOwn = false
      }
    }
    if (own && !hasOwn) {
      {
        try {
          await $.fs.write(
            own,
            `${MARKER}\n# Session board\n\nTracks what we do in this session. Stored outside any repo. Format: - [ ] todo, - [~] doing, - [x] done.\n\n## Now\n`,
          )
        } catch {
          /* the pane will show why */
        }
      }
    }
    await startPolling($)
    const r = await $.ui.open({ id: PANE, title: 'Board' })
    const pres = e.presentation
    const hint =
      pres && !pres.isFullscreen
        ? ' Shown inline above the prompt: the side pane needs fullscreen rendering (run /tui fullscreen).'
        : pres && pres.columns < 110
          ? ' Terminal under 110 columns: the side pane needs more width.'
          : ''
    return { text: (r.isPlaced ? 'Board opened.' : 'Pane waits: terminal too narrow.') + hint }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const src = await read($, text)
    if (src.startsWith(NOBOARD)) {
      return (
        <Box flexDirection="column">
          <Text>No board for this session yet. Run /session-board again to create one.</Text>
          <Text dimColor>{src.slice(NOBOARD.length)}</Text>
        </Box>
      )
    }
    if (src === '') return <Text dimColor>Loading...</Text>
    const rows = parse(src)
    const items = rows.filter(r => r.kind === 'todo' || r.kind === 'doing' || r.kind === 'done')
    const done = items.filter(r => r.kind === 'done').length
    const pct = items.length === 0 ? 0 : Math.round((done / items.length) * 100)
    const width = Math.max(10, Math.min(30, (e.props.bodyColumns ?? 30) - 12))
    const filled = Math.round((pct / 100) * width)
    return (
      <Box flexDirection="column">
        <Text bold>
          {pct}% {'█'.repeat(filled)}{'░'.repeat(width - filled)} {done}/{items.length}
        </Text>
        <Text dimColor>click pane or ctrl+x tab, then arrows/wheel to scroll</Text>
        {rows.map(r =>
          r.kind === 'h' ? (
            <Text bold color="cyan">{r.label}</Text>
          ) : r.kind === 'note' ? (
            <Text dimColor>{r.label}</Text>
          ) : (
            <Text dimColor={r.kind === 'done'} color={r.kind === 'doing' ? 'yellow' : undefined}>
              {r.kind === 'done' ? '[x]' : r.kind === 'doing' ? '[~]' : '[ ]'} {r.label}
            </Text>
          ),
        )}
      </Box>
    )
  })
}
