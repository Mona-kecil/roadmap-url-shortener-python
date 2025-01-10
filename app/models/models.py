import sqlite3
import string
import random


def main():
    print("Hello from models.py")
    print("You're not supposed to run this file directly.")


def generate_random_shortened_url() -> str:
    string = "".join(random.choice(string.ascii_letters + string.digits)
                     for _ in range(10))
    return string


def get_connection() -> sqlite3.dbapi2.Connection:
    """
    Returns a connection object to the database.
    rows are treated as dictionaries
    """
    conn = sqlite3.connect("data.db").row_factory
    return conn


def create_new_entry(
        original_url: str,
        shortened_url: str | None = None
):
    if shortened_url is None:
        shortened_url = generate_random_shortened_url()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO urls (original_url, shortened_url)
        VALUES (?, ?)
        RETURNING *;
        """
    )

    conn.commit()
    return cursor.fetchone()


def batch_create_new_entries(
    original_urls: list[str],
    shortened_urls: list[str] = None
):
    if shortened_urls is None:
        shortened_urls = [generate_random_shortened_url()
                          for _ in range(len(original_urls))]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO urls (original_url, shortened_url)
        VALUES (?, ?)
        RETURNING *;
        """,
        zip(original_urls, shortened_urls)
    )
    conn.commit()
    return cursor.fetchall()


def get_entry_by_id(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM urls WHERE id = ?
        AND deleted_at IS NULL
        """, (id,)
    )
    return cursor.fetchone()


def get_all_entries():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM urls
        WHERE deleted_at IS NULL
        """
    )
    return cursor.fetchall()


def update_entry(id: int, original_url: str, shortened_url: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
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
    conn.commit()
    return cursor.fetchone()


def delete_entry(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE urls
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = ?
        RETURNING *;
        """, (id,)
    )
    conn.commit()
    return cursor.fetchone()


if __name__ == "__main__":
    main()
