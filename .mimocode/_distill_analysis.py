import sqlite3, json
from collections import Counter, defaultdict

db = r'C:\Users\Sanket Ghosh\.local\share\mimocode\mimocode.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Current project ID
c.execute("SELECT id, name, worktree FROM project ORDER BY time_updated DESC LIMIT 5")
projects = c.fetchall()
print("=== PROJECTS ===")
for p in projects:
    print(f"  {p['id']} | {p['name']} | {p['worktree']}")
print()

# Get the project for this workspace
current_worktree = r'C:\Users\Sanket Ghosh\Documents\Code\sanketghosh.github.io'
c.execute("SELECT id FROM project WHERE worktree = ?", (current_worktree,))
proj = c.fetchone()
if not proj:
    print("Project not found, using most recent")
    proj = projects[0] if projects else None

if proj:
    project_id = proj['id']
    print(f"Using project: {project_id}")
    print()

    # Get sessions for this project
    cutoff_ms = 1749696000000  # ~June 12, 2026 (30 days before Jul 16)
    c.execute("""
        SELECT id, title, time_created, time_updated
        FROM session
        WHERE project_id = ?
        ORDER BY time_created DESC
        LIMIT 30
    """, (project_id,))
    sessions = c.fetchall()
    print(f"=== SESSIONS (project: {project_id}) ===")
    print(f"Found: {len(sessions)} sessions")
    for s in sessions:
        print(f"  {s['id']} | {s['title']} | created={s['time_created']} updated={s['time_updated']}")
    print()

    # Get all assistant tool usage across sessions in this project (last 30 days)
    session_ids = [s['id'] for s in sessions]
    if session_ids:
        placeholders = ','.join('?' * len(session_ids))
        c.execute(f"""
            SELECT json_extract(p.data, '$.tool') as tool,
                   substr(json_extract(p.data, '$.state.input'), 1, 200) as input_preview,
                   count(*) as n
            FROM message m
            JOIN part p ON p.message_id = m.id
            WHERE json_extract(m.data, '$.role') = 'assistant'
              AND json_extract(p.data, '$.type') = 'tool'
              AND m.session_id IN ({placeholders})
            GROUP BY tool, input_preview
            ORDER BY n DESC
            LIMIT 50
        """, session_ids)
        tools = c.fetchall()
        print("=== TOP TOOL USAGE (assistant turns, by input pattern) ===")
        for t in tools:
            print(f"  [{t['n']}x] {t['tool']}: {t['input_preview'][:150]}")
        print()

    # Get user message patterns (looking for repeated requests)
    if session_ids:
        c.execute(f"""
            SELECT json_extract(m.data, '$.content') as content,
                   m.session_id,
                   m.time_created
            FROM message m
            WHERE json_extract(m.data, '$.role') = 'user'
              AND m.session_id IN ({placeholders})
            ORDER BY m.time_created DESC
            LIMIT 50
        """, session_ids)
        user_msgs = c.fetchall()
        print("=== USER MESSAGES (last 50) ===")
        for u in user_msgs:
            content = u['content'] or ''
            if isinstance(content, list):
                text_parts = [p.get('text', '') for p in content if isinstance(p, dict)]
                content = ' '.join(text_parts)
            preview = content[:200].replace('\n', ' ')
            print(f"  [{u['session_id'][:12]}] {preview}")
        print()

    # Get distinct tool names used
    if session_ids:
        c.execute(f"""
            SELECT json_extract(p.data, '$.tool') as tool,
                   count(*) as n
            FROM message m
            JOIN part p ON p.message_id = m.id
            WHERE json_extract(m.data, '$.role') = 'assistant'
              AND json_extract(p.data, '$.type') = 'tool'
              AND m.session_id IN ({placeholders})
            GROUP BY tool
            ORDER BY n DESC
        """, session_ids)
        tool_summary = c.fetchall()
        print("=== TOOL USAGE SUMMARY ===")
        for t in tool_summary:
            print(f"  {t['tool']}: {t['n']} calls")
        print()

    # Get file paths touched
    if session_ids:
        c.execute(f"""
            SELECT json_extract(p.data, '$.state.input') as input_data
            FROM message m
            JOIN part p ON p.message_id = m.id
            WHERE json_extract(m.data, '$.role') = 'assistant'
              AND json_extract(p.data, '$.type') = 'tool'
              AND json_extract(p.data, '$.tool') = 'write'
              AND m.session_id IN ({placeholders})
        """, session_ids)
        writes = c.fetchall()
        file_counter = Counter()
        for w in writes:
            input_data = w['input_data'] or ''
            if isinstance(input_data, str):
                try:
                    input_data = json.loads(input_data)
                except:
                    pass
            if isinstance(input_data, dict):
                fp = input_data.get('file_path', '')
                if fp:
                    file_counter[fp] += 1
        print("=== FILES WRITTEN (frequency) ===")
        for fp, cnt in file_counter.most_common(30):
            print(f"  [{cnt}x] {fp}")
        print()

    # Tasks across sessions
    if session_ids:
        c.execute(f"""
            SELECT t.id, t.summary, t.status, t.session_id
            FROM task t
            WHERE t.session_id IN ({placeholders})
            ORDER BY t.created_at DESC
            LIMIT 30
        """, session_ids)
        tasks = c.fetchall()
        print("=== TASKS ===")
        for t in tasks:
            print(f"  {t['id']} | {t['status']} | {t['summary']}")
        print()

conn.close()
print("Done.")
