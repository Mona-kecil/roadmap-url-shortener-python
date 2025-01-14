import sqlite3
import string
import random


def main():
    print("Hello from models.py")
    print("You're not supposed to run this file directly.")


def generate_random_shortened_url() -> str:
    """
    Generates a random alphanumeric string of length 10.
    """
    string = "".join(random.choice(string.ascii_letters + string.digits)
                     for _ in range(10))
    return string


def get_connection():
    """
    Returns a connection object to the database.
    rows are treated as dictionaries
    """
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_new_entry(
        original_url: str,
        shortened_url: str | None = None
):
    if shortened_url is None:
        shortened_url = generate_random_shortened_url()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO urls (original_url, shortened_url)
            VALUES (?, ?)
            RETURNING *;
            """, (original_url, shortened_url)
        )
        data = cursor.fetchone()
        conn.commit()
        return dict(data)


def batch_create_new_entries(
    original_urls: list[str],
    shortened_urls: list[str] = None
):
    if shortened_urls is None:
        shortened_urls = [generate_random_shortened_url()
                          for _ in range(len(original_urls))]

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.executemany("""
            INSERT INTO urls (original_url, shortened_url)
            VALUES (?, ?)
            RETURNING *;
            """, zip(original_urls, shortened_urls)
        )
        data = cursor.fetchall()
        conn.commit()
        return dict(data)


def get_entry(shortened_url: str):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM urls WHERE shortened_url = ?
            AND deleted_at IS NULL
            """, (shortened_url,)
        )
        return dict(cursor.fetchone())


def get_all_entries():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM urls
            WHERE deleted_at IS NULL
            """)
        return dict(cursor.fetchall())


def update_entry(id: int, original_url: str, shortened_url: str):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE urls
            SET
                original_url = ?,
                shortened_url = ?
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND deleted_at IS NULL
            RETURNING *;
            """, (original_url, shortened_url, id)
        )
        data = cursor.fetchone()
        conn.commit()
        return dict(data)


def delete_entry(id: int):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE urls
            SET deleted_at = CURRENT_TIMESTAMP
            WHERE id = ?
            RETURNING *;
            """, (id,)
        )
        data = cursor.fetchone()
        conn.commit()
        return dict(data)


if __name__ == "__main__":
    main()
