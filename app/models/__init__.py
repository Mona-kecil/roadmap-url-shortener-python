from app.models.database import get_connection


def initialize_structure():
    with get_connection() as conn:
        print("Establishing connection to database...")
        print("Connection established.")
        cursor = conn.cursor()

        # Create the main table if not exists
        print("Creating urls table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                shortened_url TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                deleted_at TIMESTAMP
            )
            """)
        conn.commit()
        print("Table created.")

        # Create trigger to make sure that the shortened_url is unique on creation
        print("Creating unique_shortened_url_on_create trigger...")
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS unique_shortened_url_on_create
            BEFORE INSERT ON urls
            FOR EACH ROW
            BEGIN
                SELECT RAISE(ABORT, 'Shortened URL already exists.')
                WHERE EXISTS (
                    SELECT 1
                    FROM urls
                    WHERE shortened_url = NEW.shortened_url AND deleted_at IS NULL
                );
            END;
            """)
        conn.commit()
        print("Trigger created.")

        # Create trigger to make sure that the shortened_url is unique on update
        print("Creating unique_shortened_url_on_update trigger...")
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS unique_shortened_url_on_update
            BEFORE UPDATE ON urls
            FOR EACH ROW
            BEGIN
                SELECT RAISE(ABORT, 'Shortened URL already exists.')
                WHERE EXISTS (
                    SELECT 1
                    FROM urls
                    WHERE shortened_url = NEW.shortened_url
                        AND deleted_at IS NULL
                        AND id != NEW.id
                );
            END;
            """)
        conn.commit()
        print("Trigger created.")


initialize_structure()
