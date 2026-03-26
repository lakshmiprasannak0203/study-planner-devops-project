import unittest
from unittest.mock import patch, MagicMock
from app import app, calculate_study_streak
from datetime import datetime, timedelta, date

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


class TestStreakCalculation(unittest.TestCase):
    """Test cases for Daily Study Streak Tracker"""
    
    @patch('app.conn')
    def test_no_study_records(self, mock_conn):
        """Test streak when user has no study records"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        self.assertEqual(current_streak, 0)
        self.assertEqual(longest_streak, 0)
    
    @patch('app.conn')
    def test_single_study_day_today(self, mock_conn):
        """Test streak when user studied only today"""
        today = datetime.now().date()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(today,)]
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        self.assertEqual(current_streak, 1)
        self.assertEqual(longest_streak, 1)
    
    @patch('app.conn')
    def test_consecutive_days_current_streak(self, mock_conn):
        """Test streak with consecutive study days"""
        today = datetime.now().date()
        dates = [
            (today,),
            (today - timedelta(days=1),),
            (today - timedelta(days=2),),
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        self.assertEqual(current_streak, 3)
        self.assertEqual(longest_streak, 3)
    
    @patch('app.conn')
    def test_streak_broken_by_gap(self, mock_conn):
        """Test that streak is reset when there's a gap in study dates"""
        today = datetime.now().date()
        dates = [
            (today,),
            (today - timedelta(days=1),),
            (today - timedelta(days=3),),  # 2-day gap
            (today - timedelta(days=4),),
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        # Current streak should be 2 (today and yesterday)
        self.assertEqual(current_streak, 2)
        # Longest streak should be 2 (the most recent consecutive days)
        self.assertEqual(longest_streak, 2)
    
    @patch('app.conn')
    def test_streak_reset_no_recent_activity(self, mock_conn):
        """Test that streak is 0 when last study was more than 1 day ago"""
        today = datetime.now().date()
        dates = [
            (today - timedelta(days=3),),
            (today - timedelta(days=4),),
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        # Current streak should be 0 (gap > 1 day)
        self.assertEqual(current_streak, 0)
        # Longest streak should be 2 (consecutive days in the past)
        self.assertEqual(longest_streak, 2)
    
    @patch('app.conn')
    def test_multiple_streaks_longest_win(self, mock_conn):
        """Test that longest_streak is the maximum among all streaks"""
        today = datetime.now().date()
        dates = [
            (today - timedelta(days=0),),
            (today - timedelta(days=1),),
            (today - timedelta(days=3),),  # Gap
            (today - timedelta(days=4),),
            (today - timedelta(days=5),),
            (today - timedelta(days=6),),
            (today - timedelta(days=7),),  # Another gap
            (today - timedelta(days=8),),
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        # Current streak is 2
        self.assertEqual(current_streak, 2)
        # Longest streak is 4 (days 4, 5, 6, 7)
        self.assertEqual(longest_streak, 4)


class TestPomodoroTimer(unittest.TestCase):
    """Test cases for Pomodoro Study Timer"""
    
    @patch('app.conn')
    def test_pomodoro_page_access_authenticated(self, mock_conn):
        """Test that authenticated user can access Pomodoro timer"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        with test_client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = test_client.get('/pomodoro')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Pomodoro Study Timer', response.data)
        self.assertIn(b'25:00', response.data)
    
    @patch('app.conn')
    def test_pomodoro_page_redirect_unauthenticated(self, mock_conn):
        """Test that unauthenticated user is redirected to login"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        response = test_client.get('/pomodoro')
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    @patch('app.conn')
    def test_pomodoro_ui_elements(self, mock_conn):
        """Test that all required UI elements are present in Pomodoro timer"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        with test_client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = test_client.get('/pomodoro')
        response_text = response.data.decode()
        
        # Check for essential UI elements
        self.assertIn('Start', response_text)
        self.assertIn('Pause', response_text)
        self.assertIn('Reset', response_text)
        self.assertIn('Skip', response_text)
        self.assertIn('Completed Pomodoros', response_text)
        self.assertIn('Total Study Time', response_text)
        self.assertIn('Session Type', response_text)
    
    @patch('app.conn')
    def test_pomodoro_javascript_logic(self, mock_conn):
        """Test that Pomodoro timer has required JavaScript functions"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        with test_client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = test_client.get('/pomodoro')
        response_text = response.data.decode()
        
        # Check for JavaScript functions
        self.assertIn('function startTimer()', response_text)
        self.assertIn('function pauseTimer()', response_text)
        self.assertIn('function resetTimer()', response_text)
        self.assertIn('function skipSession()', response_text)
        self.assertIn('formatTime', response_text)
        self.assertIn('updateDisplay', response_text)
    
    @patch('app.conn')
    def test_pomodoro_timer_configuration(self, mock_conn):
        """Test that timer has correct time durations"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        with test_client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = test_client.get('/pomodoro')
        response_text = response.data.decode()
        
        # Check for correct timer values
        self.assertIn('25 * 60', response_text)  # 25 minutes study
        self.assertIn('5 * 60', response_text)   # 5 minutes break


class TestPomodoroIntegration(unittest.TestCase):
    """Integration tests for Pomodoro timer with main app"""
    
    @patch('app.conn')
    def test_pomodoro_link_in_dashboard(self, mock_conn):
        """Test that Pomodoro timer link appears in dashboard"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        # Setup mock
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = (0,)
        mock_conn.cursor.return_value = mock_cursor
        
        with test_client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = test_client.get('/')
        response_text = response.data.decode()
        
        # Check for Pomodoro link
        self.assertIn('/pomodoro', response_text)
        self.assertIn('Pomodoro Timer', response_text)
    
    @patch('app.conn')
    def test_navigation_between_pages(self, mock_conn):
        """Test that user can navigate between dashboard and Pomodoro timer"""
        app.config['TESTING'] = True
        test_client = app.test_client()
        
        # Setup mock
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = (0,)
        mock_conn.cursor.return_value = mock_cursor
        
        with test_client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        # Access dashboard
        response_dashboard = test_client.get('/')
        self.assertEqual(response_dashboard.status_code, 200)
        
        # Access Pomodoro timer
        response_pomodoro = test_client.get('/pomodoro')
        self.assertEqual(response_pomodoro.status_code, 200)


class TestCRUDSubjects(unittest.TestCase):
    """Test CRUD operations for Subjects"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_create_subject(self, mock_conn):
        """Test CREATE: Adding a new subject"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/add_subject', data={'subject_name': 'Mathematics'})
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_read_subjects(self, mock_conn):
        """Test READ: Fetching all subjects for a user"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [(1, 'Math'), (2, 'Science')],  # subjects
            [],  # sessions
            (10,),  # total hours
            [],  # study dates for streak
            [('Math', 5), ('Science', 3)],  # subject data
        ]
        mock_cursor.fetchone.return_value = (10,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Study Planner', response.data)
    
    @patch('app.conn')
    def test_update_subject(self, mock_conn):
        """Test UPDATE: Modifying an existing subject"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # User owns this subject
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post(
            '/update_subject/1',
            data={'subject_name': 'Advanced Mathematics'}
        )
        
        self.assertEqual(response.status_code, 302)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_update_subject_unauthorized(self, mock_conn):
        """Test UPDATE: Reject unauthorized update"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Different user owns this subject
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post(
            '/update_subject/1',
            data={'subject_name': 'Advanced Mathematics'}
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Unauthorized', response.data)
    
    @patch('app.conn')
    def test_delete_subject(self, mock_conn):
        """Test DELETE: Removing a subject and its sessions"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # User owns this subject
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/delete_subject/1')
        
        self.assertEqual(response.status_code, 302)
        # Verify delete queries were called
        self.assertTrue(mock_cursor.execute.called)
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_delete_subject_unauthorized(self, mock_conn):
        """Test DELETE: Reject unauthorized deletion"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Different user owns this subject
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/delete_subject/1')
        
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Unauthorized', response.data)


class TestCRUDStudySessions(unittest.TestCase):
    """Test CRUD operations for Study Sessions"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_create_study_session(self, mock_conn):
        """Test CREATE: Adding a new study session"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # Subject owner verification
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/add_session', data={
            'subject_id': 1,
            'study_date': '2026-03-26',
            'duration_hours': 2.5
        })
        
        self.assertEqual(response.status_code, 302)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_create_study_session_unauthorized_subject(self, mock_conn):
        """Test CREATE: Reject if subject doesn't belong to user"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Different user owns this subject
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/add_session', data={
            'subject_id': 1,
            'study_date': '2026-03-26',
            'duration_hours': 2.5
        })
        
        self.assertIn(b'Unauthorized', response.data)
    
    @patch('app.conn')
    def test_update_study_session(self, mock_conn):
        """Test UPDATE: Modifying an existing study session"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # Session owner verification
            (1,),  # Subject owner verification
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/update_session/1', data={
            'subject_id': 1,
            'study_date': '2026-03-27',
            'duration_hours': 3.0
        })
        
        self.assertEqual(response.status_code, 302)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_update_study_session_unauthorized_session(self, mock_conn):
        """Test UPDATE: Reject if session doesn't belong to user"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Different user owns this session
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/update_session/1', data={
            'subject_id': 1,
            'study_date': '2026-03-27',
            'duration_hours': 3.0
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Unauthorized', response.data)
    
    @patch('app.conn')
    def test_delete_study_session(self, mock_conn):
        """Test DELETE: Removing a study session"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # Session owner verification
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/delete_session/1')
        
        self.assertEqual(response.status_code, 302)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_delete_study_session_unauthorized(self, mock_conn):
        """Test DELETE: Reject unauthorized deletion"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # Different user owns this session
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.post('/delete_session/1')
        
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Unauthorized', response.data)


class TestCRUDSubjectsDeletion(unittest.TestCase):
    """Test cascade deletion of subjects with sessions"""
    
    @patch('app.conn')
    def test_delete_subject_cascade_deletes_sessions(self, mock_conn):
        """Test that deleting a subject also deletes all its sessions"""
        app.config['TESTING'] = True
        client = app.test_client()
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # User owns this subject
        mock_conn.cursor.return_value = mock_cursor
        
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = client.post('/delete_subject/1')
        
        self.assertEqual(response.status_code, 302)
        # Verify both delete operations were called
        calls = mock_cursor.execute.call_args_list
        self.assertTrue(any('DELETE FROM study_sessions' in str(call) for call in calls))
        self.assertTrue(any('DELETE FROM subjects' in str(call) for call in calls))

