from models import get_connection


def initialize_structure():
    conn = get_connection()
    cursor = conn.cursor()

    # Create the main table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            shortened_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP
        )
        """
    )
    conn.commit()

    # Create trigger to make sure that the shortened_url is unique on creation
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS unique_shortened_url_on_create
        BEFORE INSERT ON urls
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'Shortened URL already exists, please choose another one.')
            WHERE EXISTS (
                SELECT 1
                FROM urls
                WHERE shortened_url = NEW.shortened_url AND deleted_at IS NULL
            )
        """
    )
    conn.commit()

    # Create trigger to make sure that the shortened_url is unique on update
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS unique_shortened_url_on_update
        BEFORE UPDATE ON urls
        FOR EACH ROW
        BEGIN
            SELECT RAISE(ABORT, 'Shortened URL already exists, please choose another one.')
            WHERE EXISTS (
                SELECT 1
                FROM urls
                WHERE shortened_url = NEW.shortened_url
                    AND deleted_at IS NULL
                    AND id != NEW.id
            )
        """
    )


initialize_structure()
