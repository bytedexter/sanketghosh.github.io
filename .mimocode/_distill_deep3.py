import sqlite3, json
from collections import Counter

db = r'C:\Users\Sanket Ghosh\.local\share\mimocode\mimocode.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get a sample of parts from the other project to understand data format
proj_id = '0655be15-2a5a-47a6-8d7c-4ea98e07ea18'
c.execute("""
    SELECT id FROM session WHERE project_id = ?
    ORDER BY time_created LIMIT 5
""", (proj_id,))
sessions = c.fetchall()
session_ids = [s['id'] for s in sessions]

# Sample parts from first few sessions
for sid in session_ids[:3]:
    print(f"\n=== SESSION: {sid} ===")
    c.execute("""
        SELECT id, json_extract(data, '$.type') as ptype,
               json_extract(data, '$.tool') as tool,
               substr(json_extract(data, '$.state.input'), 1, 300) as input_preview,
               substr(json_extract(data, '$.text'), 1, 300) as text_preview
        FROM part
        WHERE session_id = ?
        ORDER BY time_created
        LIMIT 10
    """, (sid,))
    parts = c.fetchall()
    for p in parts:
        print(f"  part {p['id'][:12]} type={p['ptype']} tool={p['tool']}")
        if p['input_preview']:
            print(f"    input: {p['input_preview'][:200]}")
        if p['text_preview']:
            print(f"    text: {p['text_preview'][:200]}")

# Now check if there are write tool calls and what files they write
print("\n\n=== WRITE TOOL INPUTS (other project, sample) ===")
c.execute("""
    SELECT substr(json_extract(p.data, '$.state.input'), 1, 500) as inp
    FROM message m
    JOIN part p ON p.message_id = m.id
    WHERE json_extract(m.data, '$.role') = 'assistant'
      AND json_extract(p.data, '$.type') = 'tool'
      AND json_extract(p.data, '$.tool') = 'Write'
      AND m.session_id IN (SELECT id FROM session WHERE project_id = ?)
    LIMIT 10
""", (proj_id,))
writes = c.fetchall()
for w in writes:
    inp = w['inp']
    if inp:
        try:
            d = json.loads(inp)
            print(f"  file: {d.get('file_path', 'N/A')}")
        except:
            print(f"  raw: {inp[:200]}")

# Check the task table for the other project
print("\n\n=== TASKS (other project) ===")
c.execute("""
    SELECT t.id, t.summary, t.status, t.session_id
    FROM task t
    WHERE t.session_id IN (SELECT id FROM session WHERE project_id = ?)
    ORDER BY t.created_at DESC
    LIMIT 20
""", (proj_id,))
tasks = c.fetchall()
for t in tasks:
    print(f"  {t['id']} | {t['status']} | {t['summary'][:100]}")

# Check if there are any memory entries for this project
print("\n\n=== MEMORY ENTRIES ===")
c.execute("SELECT count(*) FROM memory_fts")
try:
    print(f"  memory_fts count: {c.fetchone()[0]}")
except Exception as e:
    print(f"  memory_fts error: {e}")

# Check global memory
c.execute("""
    SELECT * FROM memory_fts LIMIT 10
""")
try:
    rows = c.fetchall()
    for r in rows:
        print(f"  {r}")
except Exception as e:
    print(f"  memory_fts query error: {e}")

# Look at the builtin skills that are relevant
print("\n\n=== RELEVANT BUILTIN SKILLS ===")
builtin_skills_dir = r'C:\Users\Sanket Ghosh\.local\share\mimocode\builtin_skills\0.1.5\skills'
import os
for skill_name in os.listdir(builtin_skills_dir):
    skill_path = os.path.join(builtin_skills_dir, skill_name)
    if os.path.isdir(skill_path):
        skill_md = os.path.join(skill_path, 'SKILL.md')
        if os.path.exists(skill_md):
            with open(skill_md) as f:
                content = f.read()
            # Get the description from YAML frontmatter
            if content.startswith('---'):
                end = content.index('---', 3)
                frontmatter = content[3:end].strip()
                for line in frontmatter.split('\n'):
                    if line.startswith('description:'):
                        print(f"  {skill_name}: {line.split(':', 1)[1].strip()[:100]}")
                        break

conn.close()
print("\nDone.")
