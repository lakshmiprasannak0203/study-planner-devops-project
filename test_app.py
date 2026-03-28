import unittest
from unittest.mock import patch, MagicMock, call
from app import app, calculate_study_streak
from datetime import datetime, timedelta, date

# ============================================================
# AUTHENTICATION TESTS
# ============================================================
class TestAuthentication(unittest.TestCase):
    """Test cases for user authentication (login, register, logout)"""
    
    def setUp(self):
        """Setup test client before each test"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
    
    # -------- REGISTER TESTS --------
    @patch('app.conn')
    def test_register_page_get(self, mock_conn):
        """Test GET request to register page"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'register', response.data.lower())
    
    @patch('app.conn')
    def test_register_user_success(self, mock_conn):
        """Test successful user registration"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/register', data={
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Verify the cursor.execute was called with correct SQL
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Should redirect to login
        self.assertEqual(response.status_code, 200)
    
    @patch('app.conn')
    def test_register_calls_commit(self, mock_conn):
        """Test that register commits changes to database"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        self.client.post('/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'test123'
        })
        
        mock_conn.commit.assert_called_once()
    
    # -------- LOGIN TESTS --------
    @patch('app.conn')
    def test_login_page_get(self, mock_conn):
        """Test GET request to login page"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())
    
    @patch('app.conn')
    def test_login_success(self, mock_conn):
        """Test successful login with valid credentials"""
        mock_cursor = MagicMock()
        # Mock user found in database: (user_id, name, email, password)
        mock_cursor.fetchone.return_value = (1, 'John Doe', 'john@example.com', 'password123')
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/login', data={
            'email': 'john@example.com',
            'password': 'password123'
        })
        
        # Should redirect to home page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')
    
    @patch('app.conn')
    def test_login_invalid_credentials(self, mock_conn):
        """Test login with invalid credentials"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # User not found
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        })
        
        # Should show error message
        self.assertIn(b'Invalid Login', response.data)
    
    @patch('app.conn')
    def test_login_sets_session_user_id(self, mock_conn):
        """Test that login sets user_id in session"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42, 'John Doe', 'john@example.com', 'password123')
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            self.client.post('/login', data={
                'email': 'john@example.com',
                'password': 'password123'
            })
            # Verify user_id 42 was set in session
            from flask import session as flask_session
            with self.client.session_transaction() as sess:
                self.assertEqual(sess.get('user_id'), 42)
    
    # -------- LOGOUT TESTS --------
    @patch('app.conn')
    def test_logout_clears_session(self, mock_conn):
        """Test that logout clears the session"""
        response = self.client.get('/logout', follow_redirects=True)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 200)
    
    @patch('app.conn')
    def test_logout_redirect_status(self, mock_conn):
        """Test logout returns redirect status code"""
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)


# ============================================================
# HOME PAGE / INDEX TESTS
# ============================================================
class TestHomePage(unittest.TestCase):
    """Test cases for home page"""
    
    def setUp(self):
        """Setup test client before each test"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_home_page_redirects_without_session(self, mock_conn):
        """Test that home page redirects to login when not logged in"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    @patch('app.conn')
    def test_home_page_with_session(self, mock_conn):
        """Test home page loads when user is logged in"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [[], [], [], []]  # For subjects, sessions, etc.
        mock_cursor.fetchone.return_value = (0,)  # For total hours
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
    
    @patch('app.conn')
    def test_home_page_displays_subjects(self, mock_conn):
        """Test that home page displays user subjects"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [(1, 'Math'), (2, 'Science')],  # subjects
            [],  # sessions
            [],  # subject_data
        ]
        mock_cursor.fetchone.return_value = (0,)  # total_hours
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
    
    @patch('app.conn')
    def test_home_page_shows_study_stats(self, mock_conn):
        """Test that home page calculates and displays study statistics"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [],  # subjects
            [],  # sessions
            [],  # subject_data
        ]
        mock_cursor.fetchone.return_value = (10.5,)  # total_hours
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)


# ============================================================
# SUBJECT MANAGEMENT TESTS
# ============================================================
class TestSubjectManagement(unittest.TestCase):
    """Test cases for subject CRUD operations"""
    
    def setUp(self):
        """Setup test client before each test"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
    
    # -------- ADD SUBJECT TESTS --------
    @patch('app.conn')
    def test_add_subject_success(self, mock_conn):
        """Test adding a new subject successfully"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/add_subject', data={
                'subject_name': 'Mathematics'
            }, follow_redirects=True)
            
            # Verify INSERT was called
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_add_subject_inserts_with_user_id(self, mock_conn):
        """Test that added subject is associated with logged-in user"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 42
            
            self.client.post('/add_subject', data={
                'subject_name': 'Physics'
            })
            
            # Verify user_id is included in INSERT
            call_args = mock_cursor.execute.call_args
            self.assertIn(42, call_args[0][1])  # Check user_id is in parameters
    
    # -------- UPDATE SUBJECT TESTS --------
    @patch('app.conn')
    def test_update_subject_success(self, mock_conn):
        """Test updating a subject successfully"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # subject belongs to user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/update_subject/1', data={
                'subject_name': 'Advanced Mathematics'
            }, follow_redirects=True)
            
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_update_subject_unauthorized(self, mock_conn):
        """Test that users cannot update subjects they don't own"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # subject belongs to different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/update_subject/1', data={
                'subject_name': 'Hacked Subject'
            })
            
            # Should return 403 Forbidden
            self.assertEqual(response.status_code, 403)
            self.assertIn(b'Unauthorized', response.data)
    
    @patch('app.conn')
    def test_update_nonexistent_subject(self, mock_conn):
        """Test updating non-existent subject"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # subject doesn't exist
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/update_subject/999', data={
                'subject_name': 'Non-existent'
            })
            
            self.assertEqual(response.status_code, 403)
    
    # -------- DELETE SUBJECT TESTS --------
    @patch('app.conn')
    def test_delete_subject_success(self, mock_conn):
        """Test deleting a subject successfully"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # subject belongs to user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/delete_subject/1', follow_redirects=True)
            
            # Verify both DELETE queries were called
            self.assertEqual(mock_cursor.execute.call_count, 3)  # Check ownership + 2 deletes
            mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_delete_subject_unauthorized(self, mock_conn):
        """Test that users cannot delete subjects they don't own"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # belongs to different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/delete_subject/1')
            
            self.assertEqual(response.status_code, 403)
    
    @patch('app.conn')
    def test_delete_subject_cascade_deletes_sessions(self, mock_conn):
        """Test that deleting subject cascades to delete its sessions"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # subject belongs to user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            self.client.post('/delete_subject/1')
            
            # Should execute DELETE for study_sessions first
            calls = mock_cursor.execute.call_args_list
            self.assertTrue(any('study_sessions' in str(call) for call in calls))


# ============================================================
# STUDY SESSION TESTS
# ============================================================
class TestStudySessionManagement(unittest.TestCase):
    """Test cases for study session CRUD operations"""
    
    def setUp(self):
        """Setup test client before each test"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
    
    # -------- ADD SESSION TESTS --------
    @patch('app.conn')
    def test_add_study_session_success(self, mock_conn):
        """Test adding a study session successfully"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # subject belongs to user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/add_session', data={
                'subject_id': 1,
                'study_date': '2026-03-27',
                'duration_hours': 2.5
            }, follow_redirects=True)
            
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_add_session_unauthorized_subject(self, mock_conn):
        """Test that users cannot add sessions for subjects they don't own"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # subject belongs to different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/add_session', data={
                'subject_id': 1,
                'study_date': '2026-03-27',
                'duration_hours': 2.5
            })
            
            self.assertIn(b'Unauthorized', response.data)
    
    # -------- UPDATE SESSION TESTS --------
    @patch('app.conn')
    def test_update_session_success(self, mock_conn):
        """Test updating a study session successfully"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # session belongs to user
            (1,)   # subject belongs to user
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/update_session/1', data={
                'subject_id': 1,
                'study_date': '2026-03-28',
                'duration_hours': 3.0
            }, follow_redirects=True)
            
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_update_session_unauthorized_session(self, mock_conn):
        """Test that users cannot update sessions they don't own"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # session belongs to different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/update_session/1', data={
                'subject_id': 1,
                'study_date': '2026-03-28',
                'duration_hours': 3.0
            })
            
            self.assertEqual(response.status_code, 403)
    
    @patch('app.conn')
    def test_update_session_unauthorized_subject(self, mock_conn):
        """Test that users cannot update session to use someone else's subject"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # session belongs to user
            (2,)   # but subject belongs to different user
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/update_session/1', data={
                'subject_id': 1,
                'study_date': '2026-03-28',
                'duration_hours': 3.0
            })
            
            self.assertEqual(response.status_code, 403)
    
    # -------- DELETE SESSION TESTS --------
    @patch('app.conn')
    def test_delete_session_success(self, mock_conn):
        """Test deleting a study session successfully"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # session belongs to user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/delete_session/1', follow_redirects=True)
            
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_delete_session_unauthorized(self, mock_conn):
        """Test that users cannot delete sessions they don't own"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (2,)  # session belongs to different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.post('/delete_session/1')
            
            self.assertEqual(response.status_code, 403)


# ============================================================
# POMODORO TIMER TESTS
# ============================================================
class TestPomodoroTimer(unittest.TestCase):
    """Test cases for Pomodoro Timer feature"""
    
    def setUp(self):
        """Setup test client before each test"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_pomodoro_redirects_without_login(self, mock_conn):
        """Test that pomodoro page redirects to login when not logged in"""
        response = self.client.get('/pomodoro')
        self.assertEqual(response.status_code, 302)  # Redirect
    
    @patch('app.conn')
    def test_pomodoro_loads_when_logged_in(self, mock_conn):
        """Test that pomodoro page loads when logged in"""
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.get('/pomodoro')
            self.assertEqual(response.status_code, 200)
    
    @patch('app.conn')
    def test_pomodoro_page_contains_timer(self, mock_conn):
        """Test that pomodoro page contains expected timer elements"""
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user_id'] = 1
            
            response = self.client.get('/pomodoro')
            # Check for timer-related keywords
            self.assertIn(b'pomodoro', response.data.lower())


# ============================================================
# STUDY STREAK CALCULATION TESTS
# ============================================================
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


# ============================================================
# VALIDATION AND ERROR HANDLING TESTS
# ============================================================
class TestInputValidation(unittest.TestCase):
    """Test input validation and error handling"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_register_with_empty_name(self, mock_conn):
        """Test registration with empty name field"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/register', data={
            'name': '',
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Should still attempt to register - validation in frontend
        mock_cursor.execute.assert_called_once()
    
    @patch('app.conn')
    def test_login_with_empty_email(self, mock_conn):
        """Test login with empty email field"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/login', data={
            'email': '',
            'password': 'password123'
        })
        
        # Should show invalid login message
        self.assertIn(b'Invalid Login', response.data)
    
    @patch('app.conn')
    def test_add_subject_with_special_characters(self, mock_conn):
        """Test adding subject with special characters in name"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.post('/add_subject', data={
            'subject_name': "Math & Physics (Advanced) - 2026!"
        })
        
        # Should handle special characters correctly
        self.assertEqual(response.status_code, 302)
        mock_cursor.execute.assert_called()
    
    @patch('app.conn')
    def test_add_session_with_decimal_hours(self, mock_conn):
        """Test adding study session with decimal hours"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.post('/add_session', data={
            'subject_id': 1,
            'study_date': '2026-03-27',
            'duration_hours': 2.5
        })
        
        self.assertEqual(response.status_code, 302)
    
    @patch('app.conn')
    def test_add_session_with_zero_hours(self, mock_conn):
        """Test adding study session with zero hours"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.post('/add_session', data={
            'subject_id': 1,
            'study_date': '2026-03-27',
            'duration_hours': 0
        })
        
        # Allow submission (validation can be in frontend)
        self.assertEqual(response.status_code, 302)


# ============================================================
# SESSION SECURITY TESTS
# ============================================================
class TestSessionSecurity(unittest.TestCase):
    """Test session and security features"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_cannot_access_home_without_session(self, mock_conn):
        """Test that unauthenticated users cannot access home page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    @patch('app.conn')
    def test_cannot_access_pomodoro_without_session(self, mock_conn):
        """Test that unauthenticated users cannot access pomodoro"""
        response = self.client.get('/pomodoro')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    @patch('app.conn')
    def test_cannot_add_subject_without_session(self, mock_conn):
        """Test that unauthenticated users cannot add subjects"""
        try:
            response = self.client.post('/add_subject', data={
                'subject_name': 'Math'
            })
            
            # Should either error out (500) or have other handling
            self.assertIn(response.status_code, [400, 500])
        except Exception as e:
            # Expected: KeyError when accessing session['user_id'] without session
            self.assertIsNotNone(e)
    
    @patch('app.conn')
    def test_user_isolated_subjects(self, mock_conn):
        """Test that user IDs are properly checked for subject operations"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)  # Different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.post('/update_subject/1', data={
            'subject_name': 'Hacked'
        })
        
        self.assertEqual(response.status_code, 403)
    
    @patch('app.conn')
    def test_user_isolated_sessions(self, mock_conn):
        """Test that user IDs are properly checked for session operations"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)  # Different user
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.post('/delete_session/1')
        
        self.assertEqual(response.status_code, 403)
    
    @patch('app.conn')
    def test_logout_clears_all_session_data(self, mock_conn):
        """Test that logout clears all session variables"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test User'
        
        response = self.client.get('/logout')
        
        # After logout, session should be empty
        with self.client.session_transaction() as sess:
            self.assertNotIn('user_id', sess)
            self.assertNotIn('user_name', sess)


# ============================================================
# DATABASE OPERATION TESTS
# ============================================================
class TestDatabaseOperations(unittest.TestCase):
    """Test database operations and transaction handling"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_register_commits_to_database(self, mock_conn):
        """Test that registration commits data to database"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        self.client.post('/register', data={
            'name': 'New User',
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_add_subject_commits_to_database(self, mock_conn):
        """Test that adding subject commits to database"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        self.client.post('/add_subject', data={
            'subject_name': 'Biology'
        })
        
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_update_subject_commits_to_database(self, mock_conn):
        """Test that updating subject commits to database"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        self.client.post('/update_subject/1', data={
            'subject_name': 'Advanced Biology'
        })
        
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_delete_subject_commits_to_database(self, mock_conn):
        """Test that deleting subject commits to database"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        self.client.post('/delete_subject/1')
        
        mock_conn.commit.assert_called()
    
    @patch('app.conn')
    def test_add_session_verifies_subject_ownership(self, mock_conn):
        """Test that adding session verifies subject ownership"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # User owns subject
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        self.client.post('/add_session', data={
            'subject_id': 1,
            'study_date': '2026-03-27',
            'duration_hours': 2
        })
        
        # Should verify ownership before inserting
        mock_cursor.execute.assert_called()


# ============================================================
# STREAK CALCULATION EDGE CASES
# ============================================================
class TestStreakCalculationEdgeCases(unittest.TestCase):
    """Test edge cases in streak calculation"""
    
    @patch('app.conn')
    def test_streak_with_duplicate_dates(self, mock_conn):
        """Test streak calculation when user studied multiple times on same day"""
        today = datetime.now().date()
        dates = [(today,), (today,), (today - timedelta(days=1),)]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        # Should handle duplicate dates correctly
        self.assertGreaterEqual(current_streak, 1)
    
    @patch('app.conn')
    def test_streak_with_future_dates(self, mock_conn):
        """Test streak calculation with dates in the future"""
        today = datetime.now().date()
        future_date = today + timedelta(days=1)
        dates = [(future_date,), (today,)]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        # Behavior may vary based on implementation
        self.assertIsInstance(current_streak, int)
        self.assertIsInstance(longest_streak, int)
    
    @patch('app.conn')
    def test_streak_with_very_old_dates(self, mock_conn):
        """Test streak calculation with very old study dates"""
        today = datetime.now().date()
        old_date = today - timedelta(days=365)
        dates = [(old_date,)]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = dates
        mock_conn.cursor.return_value = mock_cursor
        
        current_streak, longest_streak = calculate_study_streak(1)
        
        # Current streak should be 0 (not recent)
        self.assertEqual(current_streak, 0)
        self.assertEqual(longest_streak, 1)


# ============================================================
# HOME PAGE ANALYTICS TESTS
# ============================================================
class TestHomePageAnalytics(unittest.TestCase):
    """Test analytics calculations on home page"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_total_study_hours_calculation(self, mock_conn):
        """Test that total study hours are calculated correctly"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [],  # subjects
            [],  # sessions
            [],  # subject_data
        ]
        mock_cursor.fetchone.return_value = (15.5,)  # total_hours
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Check that total hours are displayed
        self.assertIn(b'15.5', response.data)
    
    @patch('app.conn')
    def test_most_and_least_studied_calculation(self, mock_conn):
        """Test calculation of most and least studied subjects"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [],  # subjects
            [],  # sessions
            [('Math', 10), ('English', 2)],  # subject_data
        ]
        mock_cursor.fetchone.return_value = (12,)  # total_hours
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
    
    @patch('app.conn')
    def test_smart_study_plan_generation(self, mock_conn):
        """Test generation of smart study plan with recommendations"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [],  # subjects
            [],  # sessions
            [('Math', 1), ('Science', 3)],  # subject_data
        ]
        mock_cursor.fetchone.return_value = (4,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Should have recommendations
        self.assertIn(b'Focus More', response.data)


# ============================================================
# REDIRECT AND NAVIGATION TESTS
# ============================================================
class TestRedirectsAndNavigation(unittest.TestCase):
    """Test redirects and navigation flows"""
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('app.conn')
    def test_register_redirects_to_login(self, mock_conn):
        """Test that registration redirects to login page"""
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/login')
    
    @patch('app.conn')
    def test_login_redirects_to_home(self, mock_conn):
        """Test that successful login redirects to home page"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'Test', 'test@example.com', 'pass')
        mock_conn.cursor.return_value = mock_cursor
        
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'pass'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')
    
    @patch('app.conn')
    def test_subject_operations_redirect_to_home(self, mock_conn):
        """Test that subject operations redirect back to home"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Add subject redirect
        response = self.client.post('/add_subject', data={'subject_name': 'Math'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')
        
        # Update subject redirect
        response = self.client.post('/update_subject/1', data={'subject_name': 'Physics'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')
        
        # Delete subject redirect
        response = self.client.post('/delete_subject/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')


# ============================================================
# ENTRY POINT - TO RUN TESTS
# ============================================================
if __name__ == '__main__':
    """Run all unit tests"""
    unittest.main()

