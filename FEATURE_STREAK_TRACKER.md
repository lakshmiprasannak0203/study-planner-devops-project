# Daily Study Streak Tracker - Feature Documentation

## Overview
The Daily Study Streak Tracker motivates users to maintain consistent study habits by tracking the number of consecutive days they studied without skipping. This feature gamifies the learning process and encourages students to build a regular study routine.

## Features Implemented

### 1. **Streak Calculation Engine**
- **Function**: `calculate_study_streak(user_id)` in [app.py](app.py)
- **Logic**:
  - Retrieves all unique study dates for the logged-in user
  - Sorts dates chronologically (newest first)
  - Checks if the most recent study was today or yesterday
  - Counts consecutive days from the most recent date
  - Tracks both current streak and longest streak

### 2. **Current Streak**
- Displays the number of consecutive days the user has studied
- **Reset Condition**: Resets to 0 if the user skips a day (hasn't studied in more than 1 day)
- **Active Indicator**: Shows motivational message "Keep it going! 🔥"

### 3. **Longest Streak**
- Records the maximum consecutive days the user has ever achieved
- Persists across all study history, even if the current streak resets
- Acts as a personal best achievement tracker

## How It Works

### Data Flow
1. **User adds a study session** → Study date is recorded in `study_sessions` table
2. **Dashboard loads** → `calculate_study_streak()` is called
3. **Database query** → Fetches all distinct study dates for the user
4. **Streak calculation** → Algorithm analyzes dates for consecutive patterns
5. **Display** → Current and longest streaks are shown on the dashboard

### Algorithm Details

#### Current Streak Calculation
```
1. Get most recent study date
2. If (today - most_recent_date) > 1 day:
   → Current streak = 0 (gap detected)
3. Else:
   → Count consecutive days backwards
   → Stop when a gap is found
```

#### Longest Streak Calculation
```
1. Iterate through all study dates
2. Count consecutive dates
3. When a gap is found:
   → Store current count as potential longest
   → Reset counter
4. Return the maximum count found
```

### Example Scenarios

**Scenario 1 - Active Streak**
- Study dates: Mar 26, Mar 25, Mar 24, Mar 23
- Current Streak: 4 days ✓
- Longest Streak: 4 days

**Scenario 2 - Streak Reset**
- Study dates: Mar 26, Mar 25 (gap) Mar 22, Mar 21, Mar 20
- Current Streak: 2 days (Mar 26, Mar 25)
- Longest Streak: 3 days (Mar 22, Mar 21, Mar 20)

**Scenario 3 - Recently Broken Streak**
- Study dates: Mar 24 (no study on Mar 25, Mar 26)
- Current Streak: 0 days (>1 day gap)
- Longest Streak: 1 day

## UI/UX Components

### Dashboard Cards
1. **Current Streak Card**
   - Prominent display with fire emoji 🔥
   - Red text for high visibility
   - Motivational message
   - Border highlight

2. **Longest Streak Card**
   - Trophy emoji 🏆
   - Shows personal best achievement
   - Encourages improvement

3. **Streak Info Panel**
   - Displays how the streak mechanism works
   - Shows current status and recommendations
   - Provides motivation and guidance

### Visual Elements
- **Fire emoji (🔥)**: Indicates active engagement
- **Trophy emoji (🏆)**: Indicates achievement
- **Colors**:
  - Red: Current streak (urgent, motivational)
  - Warning/Yellow: Longest streak (achievement)
  - Green: Active status
  - Muted gray: Informational text

## Database Requirements

### Required Table
The feature requires the `study_sessions` table with:
- `user_id` (integer): Links to user account
- `study_date` (date): Date of the study session
- `subject_id` (integer): Subject studied
- `duration_hours` (numeric): Hours spent studying

No additional database schema changes are needed.

## Testing

### Test Cases Implemented
1. **No Study Records** - Returns 0, 0
2. **Single Study Day** - Returns 1, 1
3. **Consecutive Days** - Correctly counts all consecutive days
4. **Streak with Gap** - Detects gaps and calculates streaks correctly
5. **Streak Reset** - Correctly resets when gap > 1 day
6. **Multiple Streaks** - Identifies longest streak among multiple occurrences

### Run Tests
```bash
pytest test_app.py::TestStreakCalculation -v
```

## Performance Considerations

- **Database Query**: Uses `DISTINCT` for efficient unique date retrieval
- **Time Complexity**: O(n) where n = number of unique study dates
- **Space Complexity**: O(n) for storing study dates in memory
- **Scalability**: Works efficiently even with thousands of study sessions

## Future Enhancements

1. **Milestone Notifications**
   - Celebrate reaching 7-day, 30-day, 100-day streaks
   - Email/in-app notifications for achievements

2. **Streak History Graph**
   - Visual timeline of streak patterns over months
   - Heatmap showing study consistency

3. **Streak Statistics**
   - Average streak length
   - Most productive days (Monday, Tuesday, etc.)
   - Study time correlation with streak

4. **Gamification**
   - Badges for streak milestones
   - Leaderboards (if multi-user)
   - Streak challenges

5. **Smart Reminders**
   - Notify users if they're about to lose their streak
   - Suggest study time based on historical patterns

## Implementation Details

### Files Modified
1. **app.py**
   - Added `calculate_study_streak()` function
   - Updated `index()` route to calculate streaks
   - Pass `current_streak` and `longest_streak` to template

2. **templates/index.html**
   - Added Streak Analytics cards (Current & Longest)
   - Added Streak Info Panel with explanation
   - Enhanced dashboard layout to 4-column grid

3. **test_app.py**
   - Added `TestStreakCalculation` test class
   - Implemented comprehensive test cases
   - Tests cover all edge cases

### Code Structure
```
calculate_study_streak(user_id)
├── Query distinct study dates
├── Handle empty result (return 0, 0)
├── Calculate current streak
│   ├── Check for gap (today - most_recent)
│   └── Count consecutive days
└── Calculate longest streak
    ├── Iterate through all dates
    └── Track maximum streak
```

## Security & Validation

- **User Isolation**: Streaks only calculated for logged-in user's data
- **SQL Injection Protection**: Uses parameterized queries
- **Data Validation**: Handles edge cases (no records, gaps, etc.)
- **Session Management**: Verifies session before accessing user data

## Troubleshooting

### Issue: Streak shows 0 even with recent studies
**Solution**: Ensure study_date is set correctly when adding sessions. The system checks for dates within the last 2 days.

### Issue: Longest streak not updating
**Solution**: Longest streak is calculated dynamically. Refresh the page after adding a new session.

### Issue: Gap detection not working correctly
**Solution**: Verify that study dates are stored as DATE type in PostgreSQL, not TIMESTAMP.

## Conclusion
The Daily Study Streak Tracker successfully motivates users by:
- Showing real-time progress through current streak
- Recognizing achievements with longest streak tracking
- Encouraging daily consistency through gamification
- Providing clear visual feedback and motivation
