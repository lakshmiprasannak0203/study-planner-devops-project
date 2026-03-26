# Complete CRUD Operations - Study Planner

## Overview
This document describes all CRUD (Create, Read, Update, Delete) operations implemented in the Study Planner application for managing Subjects and Study Sessions.

## CRUD Operations Summary

### Subjects Management

#### 1. CREATE - Add Subject
**Route:** `POST /add_subject`
**Description:** Create a new study subject for the logged-in user

**Request:**
```
POST /add_subject
Content-Type: application/x-www-form-urlencoded

subject_name=Mathematics
```

**Backend Logic:**
- Stores subject in `subjects` table
- Associates it with the user's `user_id`
- Redirects to dashboard on success

**Database Query:**
```sql
INSERT INTO subjects (subject_name, user_id) 
VALUES (%s, %s)
```

**Frontend:**
- Text input field in "Add Subject" form
- Submit button to create

**Validations:**
- Subject name is required
- User must be authenticated

---

#### 2. READ - Get All Subjects
**Route:** `GET /`
**Description:** Fetch all subjects for the logged-in user

**Backend Logic:**
- Queries all subjects where `user_id` matches current user
- Returns list of (id, name) tuples
- Passes to index.html template

**Database Query:**
```sql
SELECT id, subject_name 
FROM subjects 
WHERE user_id=%s 
ORDER BY id
```

**Frontend Display:**
- Dropdown in "Add Study Session" form
- Dedicated "Your Subjects" card with list

**Data Returned:**
```python
[
    (1, 'Mathematics'),
    (2, 'Physics'),
    (3, 'Chemistry')
]
```

---

#### 3. UPDATE - Edit Subject
**Route:** `POST /update_subject/<subject_id>`
**Description:** Modify an existing subject name

**Request:**
```
POST /update_subject/1
Content-Type: application/x-www-form-urlencoded

subject_name=Advanced Mathematics
```

**Backend Logic:**
1. Verify subject belongs to current user
2. Update subject name in database
3. Redirect to dashboard

**Database Query:**
```sql
UPDATE subjects 
SET subject_name=%s 
WHERE id=%s AND user_id=%s
```

**Security Checks:**
- ✓ Ownership verification (user_id check)
- ✓ Returns 403 if unauthorized

**Frontend:**
- Modal dialog with subject name input
- Accessible via "Edit" button in subjects list
- Cancel and Update buttons

**Error Handling:**
```
Unauthorized: This subject does not belong to you! (403)
```

---

#### 4. DELETE - Remove Subject
**Route:** `POST /delete_subject/<subject_id>`
**Description:** Delete a subject and all associated study sessions

**Request:**
```
POST /delete_subject/1
```

**Backend Logic:**
1. Verify subject belongs to current user
2. Delete all study sessions for this subject (cascade delete)
3. Delete the subject itself
4. Redirect to dashboard

**Database Queries:**
```sql
DELETE FROM study_sessions 
WHERE subject_id=%s AND user_id=%s

DELETE FROM subjects 
WHERE id=%s AND user_id=%s
```

**Security Checks:**
- ✓ Ownership verification
- ✓ Cascade delete prevents orphaned data

**Frontend:**
- "Delete" button in subjects list
- Confirmation dialog: "Delete this subject and all its sessions?"
- Red danger button for visibility

**Error Handling:**
```
Unauthorized: This subject does not belong to you! (403)
```

---

### Study Sessions Management

#### 1. CREATE - Add Study Session
**Route:** `POST /add_session`
**Description:** Record a study session for a subject

**Request:**
```
POST /add_session
Content-Type: application/x-www-form-urlencoded

subject_id=1&study_date=2026-03-26&duration_hours=2.5
```

**Backend Logic:**
1. Verify subject belongs to current user
2. Insert session into `study_sessions` table
3. Redirect to dashboard

**Database Queries:**
```sql
SELECT user_id FROM subjects WHERE id=%s

INSERT INTO study_sessions 
(subject_id, study_date, duration_hours, user_id)
VALUES (%s, %s, %s, %s)
```

**Security Checks:**
- ✓ Subject ownership verification
- ✓ User association in insertion

**Frontend:**
- Subject dropdown selector
- Date picker input
- Duration hours input (supports decimals like 2.5)
- Submit button

**Validations:**
- Subject must exist and belong to user
- Date must be valid
- Duration must be positive number

---

#### 2. READ - Get All Study Sessions
**Route:** `GET /`
**Description:** Fetch all study sessions for the logged-in user

**Backend Logic:**
- Queries all sessions with subject information
- Joins with subjects table to get subject names
- Calculates streak information
- Passes data to template

**Database Query:**
```sql
SELECT s.id, sub.subject_name, s.study_date, s.duration_hours
FROM study_sessions s
JOIN subjects sub ON s.subject_id = sub.id
WHERE s.user_id=%s
```

**Frontend Display:**
- Interactive table with columns: ID, Subject, Date, Hours, Actions
- Color-coded rows for better readability
- Study streak cards showing progress

**Data Format:**
```python
[
    (1, 'Mathematics', datetime.date(2026, 3, 26), 2.5),
    (2, 'Physics', datetime.date(2026, 3, 25), 3.0),
]
```

---

#### 3. UPDATE - Edit Study Session
**Route:** `POST /update_session/<session_id>`
**Description:** Modify an existing study session

**Request:**
```
POST /update_session/1
Content-Type: application/x-www-form-urlencoded

subject_id=2&study_date=2026-03-27&duration_hours=3.5
```

**Backend Logic:**
1. Verify session belongs to current user
2. Verify new subject belongs to current user
3. Update session in database
4. Redirect to dashboard

**Database Queries:**
```sql
SELECT user_id FROM study_sessions WHERE id=%s

SELECT user_id FROM subjects WHERE id=%s

UPDATE study_sessions 
SET subject_id=%s, study_date=%s, duration_hours=%s 
WHERE id=%s AND user_id=%s
```

**Security Checks:**
- ✓ Session ownership verification
- ✓ Subject ownership verification
- ✓ Returns 403 if unauthorized

**Frontend:**
- Modal dialog with editable fields
- Pre-populated with current values
- Subject dropdown
- Date picker with current date
- Hours input with current value

**Error Handling:**
```
Unauthorized: This session does not belong to you! (403)
Unauthorized: This subject does not belong to you! (403)
```

---

#### 4. DELETE - Remove Study Session
**Route:** `POST /delete_session/<session_id>`
**Description:** Delete a study session

**Request:**
```
POST /delete_session/1
```

**Backend Logic:**
1. Verify session belongs to current user
2. Delete the session from database
3. Redirect to dashboard

**Database Query:**
```sql
DELETE FROM study_sessions 
WHERE id=%s AND user_id=%s
```

**Security Checks:**
- ✓ Ownership verification

**Frontend:**
- "Delete" button in session table Actions column
- Confirmation dialog: "Delete this session?"
- Red danger button

**Error Handling:**
```
Unauthorized: This session does not belong to you! (403)
```

---

## Complete CRUD Matrix

| Operation | Entity | Route | Method | Auth | Cascade |
|-----------|--------|-------|--------|------|---------|
| CREATE | Subject | `/add_subject` | POST | ✓ | - |
| READ | Subjects | `GET /` | GET | ✓ | - |
| UPDATE | Subject | `/update_subject/<id>` | POST | ✓ | - |
| DELETE | Subject | `/delete_subject/<id>` | POST | ✓ | Sessions |
| CREATE | Session | `/add_session` | POST | ✓ | - |
| READ | Sessions | `GET /` | GET | ✓ | - |
| UPDATE | Session | `/update_session/<id>` | POST | ✓ | - |
| DELETE | Session | `/delete_session/<id>` | POST | ✓ | - |

---

## Frontend UI Components

### Subjects Management
**Card: "Your Subjects"**
- Displays all subjects as a list
- Each subject shows:
  - Subject name with 📚 icon
  - Subject ID
  - Edit button (yellow, opens modal)
  - Delete button (red, with confirmation)

**Modal: Edit Subject**
- Title: "Edit Subject"
- Input field for subject name
- Cancel and Update buttons

### Sessions Management
**Table: Study Sessions**
- Columns: ID, Subject, Date, Hours, Actions
- Each row has:
  - Edit button (yellow, opens modal)
  - Delete button (red, with confirmation)

**Modal: Edit Study Session**
- Title: "Edit Study Session"
- Subject dropdown (pre-selected)
- Date picker (pre-filled)
- Duration hours input (pre-filled)
- Cancel and Update buttons

---

## Security Features

### 1. Authorization
- All operations verify user ownership
- Returns 403 Forbidden for unauthorized access
- Prevents cross-user data access

### 2. Data Validation
- Input types strictly checked
- Parameterized queries (prevent SQL injection)
- User ID always validated

### 3. Cascade Operations
- Deleting subject automatically deletes associated sessions
- Prevents orphaned records
- Maintains data integrity

### 4. Confirmation Dialogs
- Users confirm before deletion
- Reduces accidental data loss
- Shows clear action descriptions

---

## Database Schema

### Subjects Table
```sql
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Study Sessions Table
```sql
CREATE TABLE study_sessions (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id),
    study_date DATE NOT NULL,
    duration_hours DECIMAL(5,2) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Error Handling

### Authorization Errors (403)
```
"Unauthorized: This subject does not belong to you!"
"Unauthorized: This session does not belong to you!"
```

### Validation Errors
- Subject name: Required, non-empty
- Study date: Valid date format
- Duration: Positive number
- Subject selection: Must exist and belong to user

### Database Errors
- Connection failures
- Constraint violations
- Transaction errors

---

## Testing Coverage

### CRUD Tests Included
- ✓ Create subject
- ✓ Read subjects (dashboard display)
- ✓ Update subject (authorized and unauthorized)
- ✓ Delete subject (with cascade)
- ✓ Create study session
- ✓ Read study sessions
- ✓ Update study session (authorized and unauthorized)
- ✓ Delete study session
- ✓ Authorization verification
- ✓ Cascade deletion verification

### Run Tests
```bash
pytest test_app.py::TestCRUDSubjects -v
pytest test_app.py::TestCRUDStudySessions -v
pytest test_app.py::TestCRUDSubjectsDeletion -v
```

---

## Usage Examples

### Adding a Subject
1. Click dashboard
2. Enter subject name in "Add Subject" form
3. Click "Add" button
4. Subject appears in "Your Subjects" list

### Editing a Subject
1. Find subject in "Your Subjects" list
2. Click "Edit" button (yellow)
3. Update subject name in modal
4. Click "Update Subject" button
5. Modal closes, changes reflected

### Deleting a Subject
1. Find subject in "Your Subjects" list
2. Click "Delete" button (red)
3. Confirm deletion in dialog
4. Subject and all its sessions deleted
5. Dashboard refreshes

### Adding a Study Session
1. Select subject from dropdown
2. Pick study date from date picker
3. Enter duration (e.g., 2.5 for 2 hours 30 min)
4. Click "Add Session" button
5. Session appears in table, streak updates

### Editing a Study Session
1. Find session in "Study Sessions" table
2. Click "Edit" button (yellow)
3. Update subject, date, or hours in modal
4. Click "Update Session" button
5. Modal closes, changes reflected

### Deleting a Study Session
1. Find session in "Study Sessions" table
2. Click "Delete" button (red)
3. Confirm deletion in dialog
4. Session removed from table
5. Streak recalculates

---

## Performance Considerations

### Queries
- Indexed by user_id for fast filtering
- JOIN optimized for session queries
- Cascade delete efficient at scale

### Frontend
- Modal dialogs for editing (no page reload)
- AJAX loading for smooth UX
- Confirmation before destructive actions

### Database
- Parameterized queries prevent injection
- Transactions ensure consistency
- Proper indexing on user_id and foreign keys

---

## Future Enhancements

1. **Batch Operations**
   - Delete multiple sessions
   - Bulk edit subjects

2. **Undo/Redo**
   - Recover recently deleted items
   - 30-day trash bin

3. **Advanced Filtering**
   - Filter by date range
   - Filter by duration
   - Multiple subject selection

4. **Export/Import**
   - Export to CSV
   - Import from spreadsheet

5. **Versioning**
   - Track edit history
   - View previous versions
   - Restore old values

---

## Conclusion

The Study Planner now has full CRUD capability for both Subjects and Study Sessions with:
- ✓ Complete Create, Read, Update, Delete operations
- ✓ Authorization and security checks
- ✓ User-friendly modal interfaces
- ✓ Confirmation dialogs for safety
- ✓ Comprehensive test coverage
- ✓ Error handling and validation
- ✓ Cascade deletion for data integrity

All operations maintain data consistency and security across the application.
