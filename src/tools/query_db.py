"""
Query the database - demonstrate it's organized and queryable.
"""

import sqlite3
from pathlib import Path


def query_examples(db_path: str = "divineos.db"):
    """Show various queries on the database."""
    
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DATABASE QUERIES - ORGANIZED & QUERYABLE")
    print("=" * 80)
    
    # Query 1: Get all user messages
    print("\n[Query 1] All user messages:")
    print("-" * 80)
    cursor.execute("SELECT id, content FROM messages WHERE role = 'user' ORDER BY id")
    for row in cursor.fetchall():
        print(f"  [{row['id']}] {row['content'][:60]}...")
    
    # Query 2: Get all assistant responses
    print("\n[Query 2] All assistant responses:")
    print("-" * 80)
    cursor.execute("SELECT id, content FROM messages WHERE role = 'assistant' ORDER BY id")
    for row in cursor.fetchall():
        print(f"  [{row['id']}] {row['content'][:60]}...")
    
    # Query 3: Get conversation pairs (user + next assistant)
    print("\n[Query 3] Conversation pairs (Q&A):")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            u.id as user_id,
            u.content as user_msg,
            a.id as assistant_id,
            a.content as assistant_msg
        FROM messages u
        LEFT JOIN messages a ON a.id = u.id + 1
        WHERE u.role = 'user'
        ORDER BY u.id
    """)
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"\n  Pair {i}:")
        print(f"    Q: {row['user_msg']}")
        print(f"    A: {row['assistant_msg'][:70]}...")
    
    # Query 4: Message statistics
    print("\n[Query 4] Message statistics:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            role,
            COUNT(*) as count,
            AVG(LENGTH(content)) as avg_length,
            MIN(LENGTH(content)) as min_length,
            MAX(LENGTH(content)) as max_length
        FROM messages
        GROUP BY role
    """)
    for row in cursor.fetchall():
        print(f"  {row['role'].upper()}:")
        print(f"    Count: {row['count']}")
        print(f"    Avg length: {row['avg_length']:.0f} chars")
        print(f"    Min length: {row['min_length']} chars")
        print(f"    Max length: {row['max_length']} chars")
    
    # Query 5: Search by keyword
    print("\n[Query 5] Search for 'machine learning':")
    print("-" * 80)
    cursor.execute("""
        SELECT id, role, content
        FROM messages
        WHERE LOWER(content) LIKE '%machine learning%'
        ORDER BY id
    """)
    for row in cursor.fetchall():
        print(f"  [{row['id']}] {row['role'].upper()}: {row['content'][:70]}...")
    
    # Query 6: Verify data integrity
    print("\n[Query 6] Data integrity check:")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) as total FROM messages")
    total = cursor.fetchone()['total']
    print(f"  Total messages: {total}")
    
    cursor.execute("SELECT COUNT(*) as with_hash FROM messages WHERE content_hash IS NOT NULL")
    with_hash = cursor.fetchone()['with_hash']
    print(f"  Messages with hash: {with_hash}")
    
    cursor.execute("SELECT COUNT(*) as with_timestamp FROM messages WHERE timestamp IS NOT NULL")
    with_timestamp = cursor.fetchone()['with_timestamp']
    print(f"  Messages with timestamp: {with_timestamp}")
    
    if total == with_hash == with_timestamp:
        print(f"  [OK] All {total} messages have complete metadata")
    else:
        print(f"  [FAIL] Incomplete metadata detected")
    
    # Query 7: Timeline
    print("\n[Query 7] Message timeline:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            id,
            role,
            timestamp,
            LENGTH(content) as content_length,
            SUBSTR(content, 1, 40) as preview
        FROM messages
        ORDER BY id
    """)
    for row in cursor.fetchall():
        print(f"  [{row['id']}] {row['role'][0].upper()} @ {row['timestamp']}: {row['preview']}...")
    
    # Query 8: Verify sequence integrity
    print("\n[Query 8] Sequence integrity:")
    print("-" * 80)
    cursor.execute("SELECT id, timestamp FROM messages ORDER BY id")
    rows = cursor.fetchall()
    timestamps = [row['timestamp'] for row in rows]
    sorted_timestamps = sorted(timestamps)
    
    if timestamps == sorted_timestamps:
        print(f"  [OK] All {len(timestamps)} messages in chronological order")
    else:
        print(f"  [FAIL] Messages out of order")
    
    conn.close()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    query_examples()
