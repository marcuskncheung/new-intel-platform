# INT Reference Number System Documentation

## Overview
The INT Reference Number system provides professional case numbering for email intelligence management with format: **INT-001, INT-002, INT-003...**

## Features

### 1. **Auto-Generation**
- ✅ New emails automatically get next available INT number
- ✅ Numbers assigned chronologically (oldest = INT-001, newest = highest)
- ✅ Sequential numbering: INT-001, INT-002, INT-003...

### 2. **Manual Editing**
- ✅ Users can manually change INT numbers (e.g., INT-005 → INT-100)
- ✅ Format validation: Must be INT-XXX (up to 4 digits)
- ✅ Tracks who edited and when

### 3. **Duplicate Support**
- ✅ Multiple emails can share same INT number (for related cases)
- ✅ Useful for email threads or related intelligence

### 4. **Auto-Reordering**
- ✅ System can automatically reorder numbers to fill gaps
- ✅ Respects manually edited numbers (won't change them)
- ✅ Re-assigns auto-generated numbers only

## Database Schema

### New Columns Added to `email` Table

```sql
-- INT Reference Number fields
int_reference_number VARCHAR(20)      -- Display number: INT-001, INT-002, etc.
int_reference_order INTEGER           -- Numeric order for sorting: 1, 2, 3...
int_reference_manual BOOLEAN          -- True if manually edited
int_reference_updated_at DATETIME     -- Last update timestamp
int_reference_updated_by VARCHAR(100) -- Username who updated

-- Indexes for performance
CREATE INDEX idx_email_int_reference ON email(int_reference_number);
CREATE INDEX idx_email_int_order ON email(int_reference_order);
```

## Migration Instructions

### For Development (SQLite)
```bash
# Run migration locally
python migrate_add_int_reference.py
```

### For Production (Docker Container)

**Step 1: Push code to repository**
```bash
git add .
git commit -m "Add INT reference number system"
git push origin main
```

**Step 2: SSH into server and pull latest code**
```bash
ssh user@your-server
cd /path/to/project
git pull origin main
```

**Step 3: Run migration inside Docker container**
```bash
# Enter the Docker container
docker exec -it <container_name> /bin/bash

# Inside container, run migration
cd /app
python migrate_add_int_reference.py

# Exit container
exit
```

**Step 4: Restart application**
```bash
docker-compose restart
# or
docker restart <container_name>
```

### Migration Output Example
```
============================================================
  INT Reference Number Migration
  Auto-generate INT-001, INT-002... for all emails
============================================================

🔄 Starting INT Reference Number migration...
📊 Database: postgresql://...
✅ Connected to database
📋 Existing email table columns: 30

📝 Adding 5 new columns...
  ✅ Added column: int_reference_number
  ✅ Added column: int_reference_order
  ✅ Added column: int_reference_manual
  ✅ Added column: int_reference_updated_at
  ✅ Added column: int_reference_updated_by

🔍 Creating indexes...
  ✅ Created indexes

🔢 Generating INT reference numbers for existing emails...
  📧 Found 180 emails to process
  ✅ Assigned 180 new INT reference numbers
  📊 Total emails with INT numbers: 180

  📋 Sample INT numbers (oldest first):
    INT-001 - 2024-01-15 09:30:00
    INT-002 - 2024-01-15 10:45:00
    INT-003 - 2024-01-16 08:15:00
    INT-004 - 2024-01-16 14:20:00
    INT-005 - 2024-01-17 11:00:00

✅ Migration completed successfully!
📊 INT reference number system is now active
============================================================
```

## API Endpoints

### Update INT Reference Number
```http
POST /int_source/email/<email_id>/update_int_reference
Content-Type: application/json

{
  "int_reference_number": "INT-100",
  "reorder": false
}

Response:
{
  "success": true,
  "old_number": "INT-005",
  "new_number": "INT-100",
  "message": "INT reference updated: INT-005 → INT-100"
}
```

### Reorder All INT References
```http
POST /int_source/int_reference/reorder_all

Response:
{
  "success": true,
  "updated": 45,
  "message": "Successfully reordered 45 INT reference numbers"
}
```

### Get Emails by INT Reference
```http
GET /int_source/int_reference/100/emails

Response:
{
  "success": true,
  "int_reference": "INT-100",
  "count": 3,
  "emails": [
    {
      "id": 15,
      "entry_id": "AAMkAG...",
      "subject": "Complaint about Agent X",
      "sender": "complainant@example.com",
      "received": "2024-06-15 10:30:00",
      "status": "Pending",
      "int_reference_number": "INT-100",
      "int_reference_manual": true
    },
    ...
  ]
}
```

## Usage Examples

### Frontend JavaScript Example
```javascript
// Update INT reference number
async function updateIntReference(emailId, newIntNumber) {
  const response = await fetch(`/int_source/email/${emailId}/update_int_reference`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      int_reference_number: newIntNumber,
      reorder: false
    })
  });
  
  const result = await response.json();
  if (result.success) {
    alert(`✅ ${result.message}`);
    location.reload(); // Refresh to show updated number
  } else {
    alert(`❌ Error: ${result.error}`);
  }
}

// Example usage
updateIntReference(167, 'INT-200');
```

### Display INT Number in Email List
```html
<!-- In email list template -->
<tr>
  <td>
    <span class="badge bg-primary">{{ email.int_reference_number or 'Pending' }}</span>
  </td>
  <td>{{ email.subject }}</td>
  <td>{{ email.sender }}</td>
  <td>{{ email.received }}</td>
</tr>
```

### Editable INT Number Field
```html
<!-- In email detail page -->
<div class="int-reference-section">
  <label>Intelligence Reference Number:</label>
  <input type="text" 
         id="int-reference-input" 
         value="{{ email.int_reference_number }}"
         pattern="INT-\d{1,4}"
         placeholder="INT-001">
  <button onclick="saveIntReference({{ email.id }})">Save</button>
  
  {% if email.int_reference_manual %}
  <span class="badge bg-warning">Manually Edited</span>
  <small>Last updated by {{ email.int_reference_updated_by }} 
         on {{ email.int_reference_updated_at }}</small>
  {% endif %}
</div>

<script>
function saveIntReference(emailId) {
  const newNumber = document.getElementById('int-reference-input').value.toUpperCase();
  
  // Validate format
  if (!/^INT-\d{1,4}$/.test(newNumber)) {
    alert('Invalid format! Use INT-XXX (e.g., INT-001, INT-123)');
    return;
  }
  
  updateIntReference(emailId, newNumber);
}
</script>
```

## Workflow Scenarios

### Scenario 1: New Email Import
```
1. Exchange server imports new email
2. System detects it's new (not in database)
3. Auto-generates INT reference:
   - Finds highest order: 180
   - Assigns INT-181
4. Email saved with INT-181
```

### Scenario 2: Manual Edit
```
1. User views Email ID 50 (INT-050)
2. User changes to INT-200 (related to another case)
3. System:
   - Validates format ✓
   - Updates: INT-050 → INT-200
   - Sets int_reference_manual = True
   - Records username and timestamp
4. Other emails keep their numbers
```

### Scenario 3: Bulk Reorder
```
Before:
INT-001, INT-002, INT-005, INT-200, INT-007, INT-008

After Reorder:
INT-001 (auto)
INT-002 (auto)
INT-003 (auto, was INT-005)
INT-004 (auto, was INT-007)
INT-005 (auto, was INT-008)
INT-200 (manual, unchanged)
```

### Scenario 4: Duplicate INT Numbers
```
Email 50: INT-100 (Joe Lui bribery case - original)
Email 75: INT-100 (Joe Lui case - follow-up)
Email 92: INT-100 (Joe Lui case - additional evidence)

All three emails can share INT-100 to group them as same case.
```

## Helper Functions

### Python Backend Functions

```python
# Auto-generate INT number for new email
generate_int_reference_for_new_email(email)
# Returns: "INT-181"

# Manually update INT number
update_int_reference_number(
    email_id=167,
    new_int_number="INT-200",
    updated_by="admin_user"
)
# Returns: {'success': True, 'old_number': 'INT-050', 'new_number': 'INT-200'}

# Reorder all INT numbers
reorder_int_references_after_change()
# Returns: {'success': True, 'updated': 45}

# Get emails by INT reference
get_emails_by_int_reference("INT-100")
# Returns: [Email(...), Email(...), ...]
```

## Troubleshooting

### Issue: Migration fails with "column already exists"
```bash
# Safe - migration script checks for existing columns
# Will skip adding columns that already exist
python migrate_add_int_reference.py
```

### Issue: INT numbers not appearing
```bash
# Re-run generation for existing emails
python migrate_add_int_reference.py

# Or via Python shell
python
>>> from app1_production import app, db, Email
>>> from app1_production import generate_int_reference_for_new_email
>>> with app.app_context():
...     for email in Email.query.filter_by(int_reference_number=None).all():
...         generate_int_reference_for_new_email(email)
...     db.session.commit()
```

### Issue: Numbers out of order after manual edits
```bash
# Run reorder command
curl -X POST http://localhost:5000/int_source/int_reference/reorder_all
```

## Best Practices

1. **Use Manual Edit Sparingly**: Let auto-generation handle most cases
2. **Group Related Cases**: Use same INT number for email threads
3. **Document Manual Changes**: System tracks who/when, but add notes in comments
4. **Regular Reordering**: Run reorder monthly to maintain clean sequence
5. **Backup Before Reorder**: Reordering changes auto-generated numbers

## Security Notes

- ✅ Login required for all INT reference operations
- ✅ Username tracked for audit trail
- ✅ Format validation prevents injection
- ✅ Database transactions ensure consistency

## Performance Considerations

- Indexed columns for fast lookups
- Bulk operations use batch queries
- No impact on email import speed
- Minimal storage overhead (20 bytes per email)

## Future Enhancements

- [ ] INT number search/filter in email list
- [ ] Bulk assign same INT to multiple emails (UI)
- [ ] INT number history/audit log
- [ ] Export reports grouped by INT reference
- [ ] Dashboard widget showing INT number statistics

---

**Last Updated**: 2025-10-14  
**Version**: 1.0.0  
**Author**: Intelligence Platform Team
