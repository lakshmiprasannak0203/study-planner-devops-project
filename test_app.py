import unittest
from unittest.mock import patch, MagicMock
from app import app

class TestStudyPlanner(unittest.TestCase):
    @patch('app.conn')
    def test_home_page(self, mock_conn):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        test_client = app.test_client()
        
        # Setup mock
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = (0,)
        mock_conn.cursor.return_value = mock_cursor
        
        response = test_client.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.conn')
    def test_login_page(self, mock_conn):
        app.config['TESTING'] = True
        test_client = app.test_client()
        response = test_client.get('/login')
        self.assertEqual(response.status_code, 200)

    @patch('app.conn')
    def test_register_page(self, mock_conn):
        app.config['TESTING'] = True
        test_client = app.test_client()
        response = test_client.get('/register')
        self.assertEqual(response.status_code, 200)

    @patch('app.conn')
    def test_logout_redirect(self, mock_conn):
        app.config['TESTING'] = True
        test_client = app.test_client()
        response = test_client.get('/logout')
        self.assertEqual(response.status_code, 302)
