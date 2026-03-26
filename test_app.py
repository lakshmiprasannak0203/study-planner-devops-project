import unittest
from unittest.mock import patch
from app import app

class TestStudyPlanner(unittest.TestCase):
    @patch('app.conn')
    def setUp(self, mock_conn):
        app.config['TESTING'] = True
        self.app = app.test_client()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = (0,)

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)

    def test_logout_redirect(self):
        response = self.app.get('/logout')
        self.assertEqual(response.status_code, 302)

if __name__ == '__main__':
    unittest.main()
