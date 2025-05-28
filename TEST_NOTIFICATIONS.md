# Testing Notification Logic

## The Problem (Fixed)
Previously, the script would send notifications repeatedly for the same status, causing notification spam.

## The Solution
The script now tracks `last_notification_sent` separately from `last_status` to ensure notifications are only sent when the status actually changes.

## How to Test

### 1. Dry Run Mode (Recommended)
Test without sending actual notifications:

```bash
# Test single check
python ticket_checker.py --single --dry-run

# Test continuous monitoring (with faster interval for testing)
python ticket_checker.py --interval 60 --dry-run --config config.json
```

### 2. What You Should See

#### ✅ Correct Behavior (Fixed)
```
INFO - 🎫 Tickets became available! (was: None)
INFO - 📤 DRY RUN notification sent for status: TICKETS_AVAILABLE
DEBUG - 🔇 No notification sent - status: TICKETS_AVAILABLE (consecutive: 2)
DEBUG - 🔇 No notification sent - status: TICKETS_AVAILABLE (consecutive: 3)
INFO - ⚠️ Tickets no longer available: TICKETS_AVAILABLE → NO_TICKETS
INFO - 📤 DRY RUN notification sent for status: NO_TICKETS
```

#### ❌ Old Behavior (Bug)
```
INFO - 🎫 Tickets became available!
INFO - 📤 Notification sent for status: TICKETS_AVAILABLE
INFO - 🎫 Tickets became available!  # ← WRONG! Repeated notification
INFO - 📤 Notification sent for status: TICKETS_AVAILABLE  # ← SPAM!
```

### 3. Key Improvements

1. **Separate Tracking**: 
   - `last_status`: Tracks what status we last saw
   - `last_notification_sent`: Tracks what status we last sent a notification for

2. **Consecutive Counter**: 
   - Shows how many times we've seen the same status in a row
   - Helps with debugging

3. **Clear Logging**:
   - `📤 ACTUAL notification sent` - Real notification sent
   - `📤 DRY RUN notification sent` - Test mode
   - `🔇 No notification sent` - Status unchanged, no spam

### 4. Test Scenarios

#### Scenario 1: Status Changes (Should Send Notifications)
```
NO_TICKETS → TICKETS_AVAILABLE → NO_TICKETS
    ↓               ↓                ↓
   None        ✅ Send         ✅ Send
```

#### Scenario 2: Status Stays Same (Should NOT Send)
```
TICKETS_AVAILABLE → TICKETS_AVAILABLE → TICKETS_AVAILABLE
        ↓                   ↓                   ↓
   ✅ Send              ❌ No Send         ❌ No Send
```

### 5. Notification Modes

#### Default Mode (`--notify-all` NOT used)
- ✅ Sends notification when tickets become available
- ✅ Sends notification when tickets become unavailable (optional)
- ❌ Does NOT spam for same status

#### All Status Mode (`--notify-all` used)
- ✅ Sends notification for ANY status change
- ❌ Does NOT spam for same status

### 6. Debugging Commands

```bash
# Check what notifications would be sent
python ticket_checker.py --dry-run --single

# Test with all status notifications
python ticket_checker.py --dry-run --notify-all --interval 60

# Show current environment
python ticket_checker.py --show-env

# Test actual notifications (be careful!)
python ticket_checker.py --test-notifications
```

### 7. Railway Deployment

For Railway, the improved logic means:
- ✅ You'll only get notified when tickets actually become available
- ✅ No more notification spam for the same status
- ✅ Clear logs showing when notifications are sent vs. skipped
- ✅ Better tracking of status changes

The key fix is that the script now distinguishes between "seeing the same status" and "already notified about this status", preventing duplicate notifications! 🎉 