"""
Local SQLite database - works instantly, no Supabase setup needed!
Auto-creates tables and seeds sample data on first run.
"""
import sqlite3
import uuid
from datetime import datetime, timezone

DB_PATH = "local_database.db"


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables and seed sample data."""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            role TEXT DEFAULT 'member',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Sites table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            radius_meters INTEGER DEFAULT 15,
            address TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Site members (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_members (
            site_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            assigned_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (site_id, user_id),
            FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Seed sample users (only if empty)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            (str(uuid.uuid4()), "John Doe", "john@example.com", "+1234567890", "admin"),
            (str(uuid.uuid4()), "Jane Smith", "jane@example.com", "+0987654321", "manager"),
            (str(uuid.uuid4()), "Bob Wilson", "bob@example.com", "+1122334455", "member"),
            (str(uuid.uuid4()), "Alice Brown", "alice@example.com", "+5566778899", "member"),
            (str(uuid.uuid4()), "Charlie Davis", "charlie@example.com", "+9988776655", "member"),
        ]
        cursor.executemany(
            "INSERT INTO users (id, name, email, phone, role) VALUES (?, ?, ?, ?, ?)",
            sample_users,
        )
        print(f"Seeded {len(sample_users)} sample users")

    conn.commit()
    conn.close()
    print("Local database ready!")


# ──────────────────────────────────────────────
# HELPER: Convert Row to dict
# ──────────────────────────────────────────────
def row_to_dict(row):
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# USER OPERATIONS
# ──────────────────────────────────────────────
def get_all_users(role=None):
    conn = get_db()
    if role:
        rows = conn.execute("SELECT * FROM users WHERE role = ? ORDER BY created_at DESC", (role,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows_to_list(rows)


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def create_user(data: dict):
    conn = get_db()
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (id, name, email, phone, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, data["name"], data["email"], data.get("phone"), data.get("role", "member"), now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# SITE OPERATIONS
# ──────────────────────────────────────────────
def get_all_sites(created_by=None):
    conn = get_db()
    if created_by:
        rows = conn.execute(
            "SELECT s.*, (SELECT COUNT(*) FROM site_members sm WHERE sm.site_id = s.id) as member_count FROM sites s WHERE s.created_by = ? ORDER BY s.created_at DESC",
            (created_by,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT s.*, (SELECT COUNT(*) FROM site_members sm WHERE sm.site_id = s.id) as member_count FROM sites s ORDER BY s.created_at DESC"
        ).fetchall()
    conn.close()
    return rows_to_list(rows)


def get_site_by_id(site_id):
    conn = get_db()
    row = conn.execute(
        "SELECT s.*, (SELECT COUNT(*) FROM site_members sm WHERE sm.site_id = s.id) as member_count FROM sites s WHERE s.id = ?",
        (site_id,),
    ).fetchone()
    conn.close()
    return row_to_dict(row)


def create_site(data: dict):
    conn = get_db()
    site_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sites (id, name, latitude, longitude, radius_meters, address, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            site_id,
            data["name"],
            data.get("latitude"),
            data.get("longitude"),
            data.get("radius_meters", 15),
            data.get("address"),
            data.get("created_by"),
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT s.*, 0 as member_count FROM sites s WHERE s.id = ?", (site_id,)
    ).fetchone()
    conn.close()
    return row_to_dict(row)


def update_site(site_id, data: dict):
    conn = get_db()
    fields = []
    values = []
    for key, val in data.items():
        if val is not None:
            fields.append(f"{key} = ?")
            values.append(val)
    if not fields:
        conn.close()
        return None
    values.append(site_id)
    conn.execute(f"UPDATE sites SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    row = conn.execute(
        "SELECT s.*, (SELECT COUNT(*) FROM site_members sm WHERE sm.site_id = s.id) as member_count FROM sites s WHERE s.id = ?",
        (site_id,),
    ).fetchone()
    conn.close()
    return row_to_dict(row)


def delete_site(site_id):
    conn = get_db()
    conn.execute("DELETE FROM site_members WHERE site_id = ?", (site_id,))
    conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# SITE MEMBER OPERATIONS
# ──────────────────────────────────────────────
def get_site_members(site_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT sm.site_id, sm.user_id, sm.assigned_at, u.name as user_name, u.email as user_email
           FROM site_members sm
           JOIN users u ON u.id = sm.user_id
           WHERE sm.site_id = ?""",
        (site_id,),
    ).fetchall()
    conn.close()
    return rows_to_list(rows)


def assign_member(site_id, user_id):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO site_members (site_id, user_id, assigned_at) VALUES (?, ?, ?)",
        (site_id, user_id, now),
    )
    conn.commit()
    row = conn.execute(
        """SELECT sm.site_id, sm.user_id, sm.assigned_at, u.name as user_name, u.email as user_email
           FROM site_members sm JOIN users u ON u.id = sm.user_id
           WHERE sm.site_id = ? AND sm.user_id = ?""",
        (site_id, user_id),
    ).fetchone()
    conn.close()
    return row_to_dict(row)


def remove_member(site_id, user_id):
    conn = get_db()
    conn.execute("DELETE FROM site_members WHERE site_id = ? AND user_id = ?", (site_id, user_id))
    conn.commit()
    conn.close()


def get_available_members(site_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM site_members WHERE site_id = ?) ORDER BY name",
        (site_id,),
    ).fetchall()
    conn.close()
    return rows_to_list(rows)
