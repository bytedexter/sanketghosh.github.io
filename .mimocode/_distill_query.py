import sqlite3, json, sys

db = r'C:\Users\Sanket Ghosh\.local\share\mimocode\mimocode.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Schema of session table
c.execute("PRAGMA table_info(session)")
cols = c.fetchall()
print("session columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of message table
c.execute("PRAGMA table_info(message)")
cols = c.fetchall()
print("message columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of part table
c.execute("PRAGMA table_info(part)")
cols = c.fetchall()
print("part columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of task table
c.execute("PRAGMA table_info(task)")
cols = c.fetchall()
print("task columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of actor_registry table
c.execute("PRAGMA table_info(actor_registry)")
cols = c.fetchall()
print("actor_registry columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of task_event table
c.execute("PRAGMA table_info(task_event)")
cols = c.fetchall()
print("task_event columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of event table
c.execute("PRAGMA table_info(event)")
cols = c.fetchall()
print("event columns:", [(col['name'], col['type']) for col in cols])
print()

# Schema of project table
c.execute("PRAGMA table_info(project)")
cols = c.fetchall()
print("project columns:", [(col['name'], col['type']) for col in cols])
print()

conn.close()
