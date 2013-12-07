import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger.sqlite_handler import SQLiteHandler


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.handler = SQLiteHandler('test_db.sqlite3')

    def tearDown(self):
        self.handler.remove()

    def test_add_msg(self):
        cursor = self.handler.get_cursor()

        self.handler.add_msg(
            'irc.freenode.net',
            '#test',
            'nickname',
            'hi friends',
        )

        cursor.execute('SELECT COUNT(*), type from line;')
        result = cursor.fetchone()
        num_rows = result[0]
        self.assertEqual(num_rows, 1)

        line_type = result[1]
        self.assertEqual(line_type, 0)

    def test_add_action(self):
        cursor = self.handler.get_cursor()

        self.handler.add_action(
            'irc.freenode.net',
            '#test',
            'nickname',
            'says hi',
        )

        cursor.execute('SELECT COUNT(*), type from line;')
        result = cursor.fetchone()
        num_rows = result[0]
        self.assertEqual(num_rows, 1)

        line_type = result[1]
        self.assertEqual(line_type, 1)

    def test_add_status(self):
        cursor = self.handler.get_cursor()

        self.handler.add_status(
            'irc.freenode.net',
            '#test',
            'nickname',
            'joined #test',
        )

        cursor.execute('SELECT COUNT(*), type from line;')
        result = cursor.fetchone()
        num_rows = result[0]
        self.assertEqual(num_rows, 1)

        line_type = result[1]
        self.assertEqual(line_type, 2)

if __name__ == '__main__':
    unittest.main()
