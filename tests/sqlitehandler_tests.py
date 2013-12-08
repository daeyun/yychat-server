import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger.sqlite_handler import SQLiteHandler


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.db_manager = SQLiteHandler('test_db.sqlite3')

    def tearDown(self):
        self.db_manager.remove()

    def test_add_msg(self):
        cursor = self.db_manager.get_cursor()

        self.db_manager.add_msg(
            'irc.freenode.net',
            '#test',
            'nickname',
            'hi friends',
        )

        cursor.execute('SELECT COUNT(*), type FROM line;')
        result = cursor.fetchone()
        num_rows = result[0]
        self.assertEqual(num_rows, 1)

        line_type = result[1]
        self.assertEqual(line_type, 0)

    def test_add_action(self):
        cursor = self.db_manager.get_cursor()

        self.db_manager.add_action(
            'irc.freenode.net',
            '#test',
            'nickname',
            'says hi',
        )

        cursor.execute('SELECT COUNT(*), type FROM line;')
        result = cursor.fetchone()
        num_rows = result[0]
        self.assertEqual(num_rows, 1)

        line_type = result[1]
        self.assertEqual(line_type, 1)

    def test_add_status(self):
        cursor = self.db_manager.get_cursor()

        self.db_manager.add_status(
            'irc.freenode.net',
            '#test',
            'nickname',
            'joined #test',
        )

        cursor.execute('SELECT COUNT(*), type FROM line;')
        result = cursor.fetchone()
        num_rows = result[0]
        self.assertEqual(num_rows, 1)

        line_type = result[1]
        self.assertEqual(line_type, 2)

    def test_add_status_multiple(self):
        cursor = self.db_manager.get_cursor()
        self.db_manager.add_status(
            'irc.freenode.net',
            '#test',
            'nickname',
            'has joined #test',
        )

        self.db_manager.add_status(
            'irc.freenode.net',
            '#test',
            'nickname2',
            'has left #test',
        )

        cursor.execute('''
            SELECT type, nick, date
            FROM line
            ORDER BY date ASC
            ;
        ''')
        results = cursor.fetchall()
        result = results[1]
        self.assertEqual(len(results), 2)

        line_type = result[0]
        self.assertEqual(line_type, 2)

        nick = result[1]
        self.assertEqual(nick, 'nickname2')

if __name__ == '__main__':
    unittest.main()
