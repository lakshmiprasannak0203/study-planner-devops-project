# Selenium Automation Tests for Study Planner

## Overview
Comprehensive Selenium automation test suite for the Study Planner web application. Tests cover all major user flows including authentication, subject management, study sessions, and Pomodoro timer functionality.

## Requirements

### Prerequisites
- Python 3.8+
- Flask application running on `http://localhost:5000`
- PostgreSQL database configured and running
- Google Chrome browser installed

### Dependencies
```bash
pip install selenium webdriver-manager
```

## Test Coverage

### 1. **Application Access Tests** (3 tests)
- `test_01_home_page_redirect_to_login` - Verify unauthenticated users are redirected to login
- `test_02_register_page_accessible` - Verify register page is publicly accessible
- `test_03_login_page_accessible` - Verify login page is publicly accessible

### 2. **User Authentication Tests** (5 tests)
- `test_01_register_page_loads` - Verify register page loads with form fields
- `test_02_login_page_loads` - Verify login page loads with form fields
- `test_03_register_user_flow` - Test complete user registration flow
- `test_04_login_user_flow` - Test complete user login flow
- `test_05_logout_flow` - Test user logout flow

### 3. **Subject Management Tests** (3 tests)
- `test_01_add_subject` - Test adding a new subject
- `test_02_view_subjects_list` - Test viewing subjects list on home page
- `test_03_view_study_sessions` - Test viewing study sessions

### 4. **Pomodoro Timer Tests** (2 tests)
- `test_01_pomodoro_page_loads` - Verify Pomodoro page loads
- `test_02_pomodoro_elements_present` - Verify timer elements are present

### 5. **Performance Tests** (1 test)
- `test_01_page_load_time` - Verify pages load within acceptable time (<5s)

## Running Tests

### Quick Start
```bash
python selenium_tests.py
```

### Run with Verbose Output
```bash
python selenium_tests.py -v
```

### Run Specific Test Class
```bash
python -m unittest selenium_tests.TestUserAuthentication -v
```

### Run Specific Test
```bash
python -m unittest selenium_tests.TestUserAuthentication.test_01_register_page_loads -v
```

## Headless Mode (No Browser UI)

To run tests in headless mode (no visible browser window), uncomment this line in `selenium_tests.py`:

```python
options.add_argument('--headless')
```

## Test Database Setup

Before running tests, ensure you have test data:

```sql
-- Create test user (if not exists)
INSERT INTO users (name, email, password) 
VALUES ('Test User', 'testuser_1@example.com', 'testpass123')
ON CONFLICT DO NOTHING;

-- Add sample subjects
INSERT INTO subjects (subject_name, user_id) 
VALUES ('Mathematics', 1), ('Physics', 1), ('Chemistry', 1)
ON CONFLICT DO NOTHING;
```

## Key Features

✓ **Automatic WebDriver Management** - webdriver-manager automatically downloads and manages ChromeDriver  
✓ **Wait Strategies** - Robust wait mechanisms for dynamic content  
✓ **User Flow Testing** - Complete end-to-end user journey tests  
✓ **Access Control Testing** - Verifies authentication requirements  
✓ **Performance Monitoring** - Tracks page load times  
✓ **Comprehensive Logging** - Detailed test output for debugging  

## Troubleshooting

### ChromeDriver Issues
If you see "chromedriver not found" errors:
```bash
pip install --upgrade webdriver-manager
```

### Port Already in Use
Ensure Flask app is running on port 5000:
```bash
python app.py
```

### Selenium Timeout Errors
Increase wait timeout in the test:
```python
self.wait = WebDriverWait(cls.driver, 20)  # Change from 10 to 20
```

### Element Not Found
Check if element selectors match your HTML. Common issues:
- Form field names different than expected
- Button selectors don't match CSS/XPath
- Element IDs or classes have changed

## Test Results Interpretation

- **PASS**: Test completed successfully
- **FAIL**: Test assertion failed (logic error)
- **ERROR**: Exception thrown during test (infrastructure issue)
- **SKIP**: Test was skipped (not run)

## Best Practices

1. **Run tests in order** - Some tests depend on data from previous tests
2. **Keep test data isolated** - Use unique identifiers (timestamps) for test users
3. **Monitor performance** - Note slow page loads and optimize accordingly
4. **Regular execution** - Run tests after major code changes
5. **Maintain selectors** - Update test selectors when UI changes

## Continuous Integration

To integrate with CI/CD pipeline, use the return value:

```bash
python selenium_tests.py && echo "Tests passed" || echo "Tests failed"
```

## Notes

- Tests use real browser automation (not mocks)
- Tests run sequentially to avoid race conditions
- Each test is independent and can run standalone
- Browser window stays open for manual inspection (use --headless to close automatically)
- Test results show in both terminal and Python unittest format

## Future Enhancements

- [ ] Parallel test execution
- [ ] Screenshot capture on failures
- [ ] Video recording of test runs
- [ ] Cloud-based browser testing (BrowserStack, Sauce Labs)
- [ ] API integration for faster setup/teardown
- [ ] Custom reporting HTML output
