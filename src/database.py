"""
SQLite database module for the Sorting Algorithms Visualizer.
Tracks solo-mode sort sessions: algorithm, array size, swaps,
comparisons, and elapsed time.
"""

import sqlite3
import os

# Place the database file next to this source file
_DB_PATH = os.path.join(os.path.dirname(__file__), 'leaderboard.db')


def _get_connection():
    """Return a new connection to the SQLite database."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the leaderboard table if it does not already exist."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                algorithm   TEXT    NOT NULL,
                array_size  INTEGER NOT NULL,
                swaps       INTEGER NOT NULL,
                comparisons INTEGER NOT NULL,
                elapsed_ms  REAL    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()


def save_record(algorithm: str, array_size: int, swaps: int,
                comparisons: int, elapsed_ms: float) -> int:
    """
    Insert a completed sort session into the database.

    Returns the row-id of the newly inserted record.
    """
    with _get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO leaderboard (algorithm, array_size, swaps, comparisons, elapsed_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (algorithm, array_size, swaps, comparisons, elapsed_ms),
        )
        conn.commit()
        return cur.lastrowid


def get_records(filter_algorithm: str = None,
                sort_by: str = 'elapsed_ms',
                sort_asc: bool = True,
                limit: int = 200) -> list:
    """
    Retrieve leaderboard records.

    Parameters
    ----------
    filter_algorithm : str or None
        When set, only return rows for that algorithm name.
    sort_by : str
        Column to sort by. One of: 'elapsed_ms', 'swaps', 'comparisons',
        'array_size', 'algorithm', 'created_at'.
    sort_asc : bool
        True → ascending, False → descending.
    limit : int
        Maximum number of rows to return.
    """
    valid_columns = {'elapsed_ms', 'swaps', 'comparisons',
                     'array_size', 'algorithm', 'created_at', 'id'}
    if sort_by not in valid_columns:
        sort_by = 'elapsed_ms'

    direction = 'ASC' if sort_asc else 'DESC'

    with _get_connection() as conn:
        if filter_algorithm and filter_algorithm != 'All':
            rows = conn.execute(
                f"""
                SELECT id, algorithm, array_size, swaps, comparisons,
                       elapsed_ms, created_at
                FROM leaderboard
                WHERE algorithm = ?
                ORDER BY {sort_by} {direction}
                LIMIT ?
                """,
                (filter_algorithm, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT id, algorithm, array_size, swaps, comparisons,
                       elapsed_ms, created_at
                FROM leaderboard
                ORDER BY {sort_by} {direction}
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [dict(r) for r in rows]


def get_algorithms() -> list:
    """Return a sorted list of all distinct algorithm names in the DB."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT algorithm FROM leaderboard ORDER BY algorithm"
        ).fetchall()
    return [r['algorithm'] for r in rows]


def delete_record(record_id: int):
    """Delete a single record by its id."""
    with _get_connection() as conn:
        conn.execute("DELETE FROM leaderboard WHERE id = ?", (record_id,))
        conn.commit()


def export_csv(filepath: str,
               filter_algorithm: str = None,
               sort_by: str = 'elapsed_ms',
               sort_asc: bool = True,
               limit: int = None) -> int:
    """
    Write the current leaderboard records to a CSV file.

    Parameters match get_records() for consistent filtering/sorting.
    Returns the number of rows written.
    """
    import csv

    # If limit is None, we pass a very large number to get_records
    # (or we could update get_records to handle None for limit)
    fetch_limit = limit if limit is not None else 1_000_000

    records = get_records(filter_algorithm=filter_algorithm,
                          sort_by=sort_by,
                          sort_asc=sort_asc,
                          limit=fetch_limit)

    fieldnames = ['id', 'algorithm', 'array_size', 'swaps',
                  'comparisons', 'elapsed_s', 'created_at']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow({
                'id':          rec['id'],
                'algorithm':   rec['algorithm'],
                'array_size':  rec['array_size'],
                'swaps':       rec['swaps'],
                'comparisons': rec['comparisons'],
                'elapsed_s':   f"{rec['elapsed_ms'] / 1000:.3f}",
                'created_at':  rec['created_at'],
            })

    return len(records)


# Initialise the schema on first import
init_db()
