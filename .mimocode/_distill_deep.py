import sqlite3, json
from collections import Counter, defaultdict

db = r'C:\Users\Sanket Ghosh\.local\share\mimocode\mimocode.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Check the OTHER project too
c.execute("SELECT id, worktree FROM project ORDER BY time_updated DESC LIMIT 5")
projects = c.fetchall()
print("=== ALL PROJECTS ===")
for p in projects:
    print(f"  {p['id']} | {p['worktree']}")
print()

# Check other project sessions
for proj in projects:
    if proj['id'] == 'global':
        continue
    c.execute("""
        SELECT id, title, time_created, time_updated
        FROM session
        WHERE project_id = ?
        ORDER BY time_created DESC
        LIMIT 20
    """, (proj['id'],))
    sessions = c.fetchall()
    print(f"=== SESSIONS for {proj['id']} ({len(sessions)} total) ===")
    for s in sessions:
        print(f"  {s['id']} | {s['title']} | created={s['time_created']}")
    print()

# Also look at user messages more carefully - the content field may be JSON array
c.execute("""
    SELECT json_extract(m.data, '$.role') as role,
           json_extract(m.data, '$.content') as content,
           m.session_id,
           m.time_created
    FROM message m
    WHERE m.session_id IN (
        SELECT id FROM session WHERE project_id = '14801352-1373-4594-bbf4-460df9a9d627'
    )
    ORDER BY m.time_created
    LIMIT 30
""")
rows = c.fetchall()
print("=== ALL MESSAGES (this project) ===")
for r in rows:
    role = r['role']
    content = r['content']
    sid = r['session_id']
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except:
            pass
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    texts.append(item.get('text', '')[:200])
        preview = ' | '.join(texts)[:300]
    elif isinstance(content, str):
        preview = content[:300]
    else:
        preview = str(content)[:300]
    print(f"  [{role}] [{sid[:12]}] {preview}")
print()

# Check memory files for this project
c.execute("""
    SELECT key, type, substr(body, 1, 200) as body_preview
    FROM memory_fts
    LIMIT 10
""")
try:
    mem_rows = c.fetchall()
    print("=== MEMORY FTS ENTRIES ===")
    for m in mem_rows:
        print(f"  {m['key']} | {m['type']} | {m['body_preview']}")
except Exception as e:
    print(f"Memory FTS error: {e}")
print()

# Check global memory
import os
mem_root = r'C:\Users\Sanket Ghosh\.local\share\mimocode\memory'
for root, dirs, files in os.walk(mem_root):
    for f in files:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            print(f"  MEMORY FILE: {fp}")

conn.close()
print("\nDone.")
