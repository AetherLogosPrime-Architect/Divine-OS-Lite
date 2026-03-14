"""
Inspect database contents and verify 1:1 lossless copy.
"""

import sqlite3
import json
from pathlib import Path


def inspect_database(db_path: str = "divineos.db"):
    """Inspect and display database contents."""
    
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DATABASE INSPECTION")
    print("=" * 80)
    
    # Get message count
    cursor.execute("SELECT COUNT(*) as count FROM messages")
    msg_count = cursor.fetchone()["count"]
    print(f"\nTotal messages stored: {msg_count}")
    
    # Display all messages
    print("\n" + "-" * 80)
    print("MESSAGES IN DATABASE")
    print("-" * 80)
    
    cursor.execute("""
        SELECT id, role, content, content_hash, timestamp, message_type
        FROM messages
        ORDER BY id ASC
    """)
    
    messages = cursor.fetchall()
    
    for i, row in enumerate(messages, 1):
        print(f"\n[Message {i}]")
        print(f"  ID: {row['id']}")
        print(f"  Role: {row['role']}")
        print(f"  Type: {row['message_type']}")
        print(f"  Timestamp: {row['timestamp']}")
        print(f"  Hash: {row['content_hash']}")
        print(f"  Content ({len(row['content'])} chars):")
        
        # Display content with line breaks
        content_lines = row['content'].split('\n')
        for line in content_lines:
            print(f"    {line}")
    
    # Verify hashes
    print("\n" + "-" * 80)
    print("HASH VERIFICATION")
    print("-" * 80)
    
    import hashlib
    all_valid = True
    
    for row in messages:
        computed = hashlib.sha256(row['content'].encode()).hexdigest()
        stored = row['content_hash']
        valid = computed == stored
        all_valid = all_valid and valid
        
        status = "[OK]" if valid else "[FAIL]"
        print(f"{status} Message {row['id']}: {stored[:16]}... {'VALID' if valid else 'CORRUPTED'}")
    
    if all_valid:
        print("\n[OK] All hashes verified - no corruption detected")
    else:
        print("\n[FAIL] Hash verification failed - data corruption detected")
    
    # Check for tool calls/results
    cursor.execute("SELECT COUNT(*) as count FROM tool_calls")
    tool_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM tool_results")
    result_count = cursor.fetchone()["count"]
    
    print(f"\nTool calls stored: {tool_count}")
    print(f"Tool results stored: {result_count}")
    
    # Database schema
    print("\n" + "-" * 80)
    print("DATABASE SCHEMA")
    print("-" * 80)
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        print(f"\n{row['sql']}")
    
    # Summary statistics
    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)
    
    cursor.execute("SELECT role, COUNT(*) as count FROM messages GROUP BY role")
    role_counts = cursor.fetchall()
    
    print("\nMessages by role:")
    for row in role_counts:
        print(f"  {row['role']}: {row['count']}")
    
    total_chars = sum(len(row['content']) for row in messages)
    print(f"\nTotal characters stored: {total_chars}")
    print(f"Average message length: {total_chars // len(messages) if messages else 0} chars")
    
    conn.close()
    
    print("\n" + "=" * 80)


def compare_with_original(original_file: str, db_path: str = "divineos.db"):
    """Compare original file with database contents."""
    
    print("\n" + "=" * 80)
    print("COMPARISON: ORIGINAL vs DATABASE")
    print("=" * 80)
    
    # Read original
    with open(original_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Parse original
    from markdown_parser import MarkdownParser
    parser = MarkdownParser()
    original_messages = parser.parse_claude_format(original_content)
    
    # Get from DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages ORDER BY id ASC")
    db_messages = cursor.fetchall()
    conn.close()
    
    print(f"\nOriginal file messages: {len(original_messages)}")
    print(f"Database messages: {len(db_messages)}")
    
    if len(original_messages) != len(db_messages):
        print("✗ Message count mismatch!")
        return False
    
    print("\n" + "-" * 80)
    print("DETAILED COMPARISON")
    print("-" * 80)
    
    all_match = True
    for i, (orig, db_msg) in enumerate(zip(original_messages, db_messages), 1):
        role_match = orig["role"] == db_msg["role"]
        content_match = orig["content"] == db_msg["content"]
        
        status = "[OK]" if (role_match and content_match) else "[FAIL]"
        print(f"\n{status} Message {i}:")
        print(f"  Role: {orig['role']} == {db_msg['role']} {'[OK]' if role_match else '[FAIL]'}")
        print(f"  Content match: {'[OK]' if content_match else '[FAIL]'}")
        
        if not content_match:
            print(f"  Original length: {len(orig['content'])}")
            print(f"  DB length: {len(db_msg['content'])}")
            all_match = False
    
    print("\n" + "-" * 80)
    if all_match:
        print("[OK] PERFECT 1:1 MATCH - Lossless copy verified")
    else:
        print("[FAIL] MISMATCH DETECTED - Data loss or corruption")
    
    return all_match


if __name__ == "__main__":
    import sys
    
    # Inspect database
    inspect_database()
    
    # Compare with original
    if Path("Divine-OS-Lite/test_chat.md").exists():
        compare_with_original("Divine-OS-Lite/test_chat.md")
    elif Path("test_chat.md").exists():
        compare_with_original("test_chat.md")
