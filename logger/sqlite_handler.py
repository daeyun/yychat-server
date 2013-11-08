import sqlite3
import os


class SQLiteHandler:
    def __init__(self, filename):
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.filename = os.path.join(dirname, '../sqlite3', filename)

        if not self.isSQLite3(self.filename):
            self.conn = sqlite3.connect(self.filename)
            cursor = self.conn.cursor()

            cursor.execute('''
                CREATE TABLE message (
                id INTEGER PRIMARY KEY NOT NULL,
                date DATETIME DEFAULT current_timestamp,
                nick VARCHAR(64),
                channel VARCHAR(64),
                network VARCHAR(256),
                message TEXT(512)
                );
            ''')

            self.conn.commit()
        else:
            self.conn = sqlite3.connect(self.filename)

    def isSQLite3(self, filename):
        """http://stackoverflow.com/questions/12932607/how-to-check-with-python
        -and-sqlite3-if-one-sqlite-database-file-exists"""

        if not os.path.isfile(filename):
            return False

        # SQLite database file header is 100 bytes
        if os.path.getsize(filename) < 100:
            return False
        else:
            fd = open(filename, 'rb')
            Header = fd.read(100)
            fd.close()

            if Header[0:16] == 'SQLite format 3\000':
                return True
            else:
                return False

    def add_msg(self, network, channel, nickname, message):
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO message (nick, channel, network, message)
            VALUES (?, ?, ?, ?);
        ''', (nickname, channel, network, message))

        self.conn.commit()

    def get_cursor(self):
        return self.conn.cursor()

    def remove(self):
        os.remove(self.filename)
