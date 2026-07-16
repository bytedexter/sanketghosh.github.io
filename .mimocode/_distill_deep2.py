import sqlite3, json

db = r'C:\Users\Sanket Ghosh\.local\share\mimocode\mimocode.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Check the other project's tool usage (the one with 20 sessions)
proj_id = '0655be15-2a5a-47a6-8d7c-4ea98e07ea18'
c.execute("""
    SELECT id, title, time_created
    FROM session
    WHERE project_id = ?
    ORDER BY time_created
""", (proj_id,))
sessions = c.fetchall()
session_ids = [s['id'] for s in sessions]
print(f"=== OTHER PROJECT: {proj_id} ({len(sessions)} sessions) ===")
for s in sessions:
    print(f"  {s['id']} | {s['title'][:80]} | {s['time_created']}")
print()

# Tool usage summary for the other project
placeholders = ','.join('?' * len(session_ids))
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
print("=== OTHER PROJECT TOOL USAGE ===")
for t in tool_summary:
    print(f"  {t['tool']}: {t['n']} calls")
print()

# Files written in the other project
c.execute(f"""
    SELECT json_extract(p.data, '$.state.input') as input_data
    FROM message m
    JOIN part p ON p.message_id = m.id
    WHERE json_extract(m.data, '$.role') = 'assistant'
      AND json_extract(p.data, '$.type') = 'tool'
      AND json_extract(p.data, '$.tool') = 'write'
      AND m.session_id IN ({placeholders})
""", session_ids)
from collections import Counter
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
print("=== OTHER PROJECT FILES WRITTEN ===")
for fp, cnt in file_counter.most_common(30):
    print(f"  [{cnt}x] {fp}")
print()

# Look at the user messages for the other project to understand what they were doing
c.execute(f"""
    SELECT json_extract(m.data, '$.role') as role,
           json_extract(m.data, '$.content') as content,
           m.session_id
    FROM message m
    WHERE json_extract(m.data, '$.role') = 'user'
      AND m.session_id IN ({placeholders})
    ORDER BY m.time_created
    LIMIT 30
""", session_ids)
user_msgs = c.fetchall()
print("=== OTHER PROJECT USER MESSAGES ===")
for u in user_msgs:
    content = u['content']
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except:
            pass
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', '')[:300])
        preview = ' | '.join(texts)[:400]
    elif isinstance(content, str) and content != 'None':
        preview = content[:400]
    else:
        preview = str(content)[:400]
    print(f"  [{u['session_id'][:12]}] {preview[:300]}")
print()

# Check what memory files exist
import os
mem_root = r'C:\Users\Sanket Ghosh\.local\share\mimocode\memory'
for root, dirs, files in os.walk(mem_root):
    depth = root.replace(mem_root, '').count(os.sep)
    if depth > 4:
        continue
    indent = '  ' * depth
    print(f"{indent}{os.path.basename(root)}/")
    for f in files:
        print(f"{indent}  {f}")

conn.close()
print("\nDone.")
