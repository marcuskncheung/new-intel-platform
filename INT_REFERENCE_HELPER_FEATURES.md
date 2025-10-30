# INT Reference Helper Features

## 🎯 Problem Solved
Users might forget which INT references already exist with many intelligence sources, leading to:
- **Duplicate INT numbers** (assigning INT-005 when it already exists)
- **Skipped numbers** (jumping from INT-003 to INT-008)
- **Wrong grouping** (assigning wrong INT to related emails)

## ✨ New Features

### 1. **Auto-Complete Dropdown**
- As you type "INT-", shows all existing INT references
- Each suggestion shows:
  - INT number (e.g., INT-001)
  - Person name and nature (e.g., "John Doe - Unlicensed practice")
  - Number of linked sources (e.g., "3 sources")

### 2. **"Next" Button** 
- Click to auto-fill the next available INT number
- Prevents duplicate numbers
- Example: If highest is INT-047, suggests INT-048

### 3. **"Search" Button**
- Search existing INT references by:
  - Person name (English or Chinese)
  - Alleged nature
  - Email subject keywords
- Shows matching results with descriptions
- Click result to auto-fill the field

### 4. **Smart Grouping**
- Multiple emails can share same INT reference
- Email IDs remain unique
- Easy to see related incidents

## 🚀 How to Use

### On Email Detail Page:

**Scenario 1: New Incident (Need New INT)**
1. Click **"Next"** button
2. System suggests: "INT-048"
3. Click **"Assign Case"**

**Scenario 2: Related to Existing Incident**
1. Click **"Search"** button
2. Type person name: "John Doe"
3. System shows: INT-005 with description
4. Click the result to auto-fill
5. Click **"Assign Case"**

**Scenario 3: Remember the INT Number**
1. Start typing: "INT-"
2. Auto-complete dropdown shows all existing INT numbers
3. Select from dropdown
4. Click **"Assign Case"**

## 📊 Example Workflow

**Email #45** - First complaint about John Doe
- User clicks **"Next"** → Gets INT-001
- Assigns INT-001 to Email #45

**Email #46** - Follow-up about John Doe
- User clicks **"Search"** → Types "John Doe"
- Finds INT-001 (already has 1 email)
- Assigns INT-001 to Email #46
- **Now INT-001 groups 2 related emails**

**Email #47** - Different case about Mary Smith
- User clicks **"Next"** → Gets INT-002
- Assigns INT-002 to Email #47

**Result:**
- INT-001: 2 emails about John Doe (Email #45, #46)
- INT-002: 1 email about Mary Smith (Email #47)
- No duplicate or skipped numbers!

## 🔧 Technical Details

### New API Endpoints:

1. **`GET /api/int_references/list`**
   - Returns all existing INT references with descriptions
   - Used for autocomplete dropdown

2. **`GET /api/int_references/next_available`**
   - Returns next available INT number
   - Prevents duplicates

3. **`GET /api/int_references/search?q=keyword`**
   - Searches INT references by keyword
   - Returns matching results with context

### Database:
- Uses `CaseProfile` table
- Multiple emails link to same `CaseProfile` via `caseprofile_id`
- Each email keeps unique ID

## 📝 Tips

✅ **DO:**
- Use **"Next"** for new incidents
- Use **"Search"** to find related cases
- Check autocomplete suggestions before typing full number

❌ **DON'T:**
- Manually type numbers without checking (might duplicate)
- Create new INT if case already exists (search first!)

## 🔄 Deployment

After deploying to server:
```bash
cd /path/to/new-intel-platform
git pull
docker-compose restart
```

Then test on any email detail page:
1. Try the **"Next"** button
2. Try the **"Search"** button
3. Try typing "INT-" to see autocomplete

## 🎉 Benefits

- **No more duplicate INT numbers**
- **No more skipped numbers**
- **Easy to find related cases**
- **Faster assignment process**
- **Better data organization**

---

*Last Updated: October 22, 2025*
*Feature Status: ✅ Deployed and Ready*
