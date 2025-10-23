# Airtable Setup Guide

Quick reference for setting up Airtable integration in client installs.

## Required Environment Variables

Add these to Replit Secrets or `.env` file:

```bash
AIRTABLE_ACCESS_TOKEN=patXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXX
AIRTABLE_TABLE_NAME=tblYYYYYYYYYY
```

## How to Get These Values

### 1. AIRTABLE_ACCESS_TOKEN (Personal Access Token)

1. Go to https://airtable.com/create/tokens
2. Click "Create new token"
3. Give it a name (e.g., "Content Agent")
4. Add scopes:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
5. Add access to your specific base
6. Click "Create token"
7. Copy the token (starts with `pat...`)

### 2. AIRTABLE_BASE_ID

1. Open your Airtable base
2. Look at the URL: `https://airtable.com/appXXXXXXXXXX/tblYYYYYYYYYY/...`
3. The part starting with `app` is your Base ID
4. Example: `appAbC123dEfGhIj`

### 3. AIRTABLE_TABLE_NAME

1. Same URL as above
2. The part starting with `tbl` is your Table Name
3. Example: `tblXyZ789kLmNoPq`

## Required Table Fields

Your Airtable table must have these fields (exact names):

| Field Name | Type | Options | Required |
|------------|------|---------|----------|
| **Body Content** | Long text | - | Yes |
| **Platform** | Multiple select | See below | Yes |
| **Status** | Single select | See below | Yes |
| Post Hook | Long text | - | No |
| Publish Date | Date | - | No |
| Suggested Edits | Long text | - | No |
| Media/Thumbnail | URL | - | No |

### Platform Options (case-sensitive)

Make sure your Platform field has these exact options:

- `Linkedin`
- `X/Twitter`
- `Email`
- `Youtube`
- `Instagram`

### Status Options

Common options:

- `Draft`
- `Scheduled`
- `Published`
- `Archived`

**Important:** The agent uses `Draft` by default. Make sure this option exists!

## Testing Your Setup

Run this command in Replit:

```bash
python test_airtable_simple.py
```

This will:
1. Check if environment variables are set
2. Verify format of Base ID and Table Name
3. Test connection to Airtable
4. Try to create a test LinkedIn post
5. Show specific error messages if something is wrong

## Common Errors

### "Platform field doesn't have option 'Linkedin'"

**Fix:**
1. Open your Airtable table
2. Click the dropdown arrow on the "Platform" column header
3. Click "Customize field type"
4. Add missing platform options (case-sensitive!)

### "Missing Airtable credentials"

**Fix:** Make sure all three environment variables are set in Replit Secrets or `.env`

### "Permission denied" or "Forbidden"

**Fix:**
1. Go to https://airtable.com/create/tokens
2. Find your token
3. Make sure it has:
   - Write access (`data.records:write`)
   - Access to this specific base

### "Base ID format invalid"

**Fix:**
- Base ID should start with `app` (e.g., `appAbC123dEfGhIj`)
- Get it from the Airtable URL, not the table name

### "Table not found"

**Fix:**
- Table Name should start with `tbl` (e.g., `tblXyZ789kLmNoPq`)
- Get it from the Airtable URL
- Don't use the human-readable table name (like "Content Calendar")

## URL Structure

```
https://airtable.com/appAbC123dEfGhIj/tblXyZ789kLmNoPq/viwABCDEFGHIJKL
                      ^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^
                      Base ID          Table Name
```

## Platform Mapping

The agent uses these internal names → Airtable options:

| Agent Platform | Airtable Option |
|----------------|-----------------|
| `linkedin` | `Linkedin` |
| `twitter` | `X/Twitter` |
| `email` | `Email` |
| `youtube` | `Youtube` |
| `instagram` | `Instagram` |
| `blog` | `Blog` |

Make sure your Airtable Platform field has the exact options in the right column.

## Quick Client Setup Checklist

- [ ] Create Personal Access Token with write permissions
- [ ] Get Base ID from Airtable URL (starts with `app`)
- [ ] Get Table Name from Airtable URL (starts with `tbl`)
- [ ] Add all three variables to Replit Secrets
- [ ] Verify Platform field has: Linkedin, X/Twitter, Email, Youtube, Instagram
- [ ] Verify Status field has: Draft
- [ ] Run `python test_airtable_simple.py` to test
- [ ] Check Airtable for test record
- [ ] Delete test record

## Support

If you're still getting errors after checking everything above:

1. Run the test script and copy the full error message
2. Check the Replit logs for more details
3. Verify the PAT hasn't expired (tokens can be set to expire)
