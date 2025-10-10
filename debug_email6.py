#!/usr/bin/env python3
"""
Debug script to check Email 6 and its attachments
"""
from app1_production import db, Email, Attachment, CaseProfile

print("=" * 80)
print("DEBUGGING EMAIL 6 AND ATTACHMENTS")
print("=" * 80)

# Get Email 6
email6 = Email.query.get(6)
if not email6:
    print("❌ Email 6 NOT FOUND!")
    exit(1)

print(f"\n📧 EMAIL 6 DETAILS:")
print(f"   ID: {email6.id}")
print(f"   Subject: {email6.subject}")
print(f"   Sender: {email6.sender}")
print(f"   Received: {email6.received}")
print(f"   Alleged Subject: {email6.alleged_subject}")
print(f"   Alleged Nature: {email6.alleged_nature}")
print(f"\n   Body Preview (first 500 chars):")
print(f"   {email6.body[:500] if email6.body else 'NO BODY'}")

# Get attachments for Email 6
attachments = Attachment.query.filter_by(email_id=6).all()
print(f"\n📎 ATTACHMENTS FOR EMAIL 6: {len(attachments)}")
for att in attachments:
    size_mb = len(att.file_data) / (1024*1024) if att.file_data else 0
    print(f"   - ID: {att.id}")
    print(f"     Filename: {att.filename}")
    print(f"     Email ID: {att.email_id}")
    print(f"     Size: {size_mb:.1f} MB")
    print(f"     Has Data: {'✅ YES' if att.file_data else '❌ NO'}")

# Check Attachment 19 specifically
print(f"\n📎 ATTACHMENT 19 DETAILS:")
att19 = Attachment.query.get(19)
if att19:
    print(f"   Filename: {att19.filename}")
    print(f"   Email ID: {att19.email_id}")
    print(f"   Size: {len(att19.file_data)/(1024*1024):.1f} MB" if att19.file_data else "   NO DATA")
    print(f"   Belongs to Email 6: {'✅ YES' if att19.email_id == 6 else '❌ NO - WRONG EMAIL!'}")
else:
    print("   ❌ NOT FOUND")

# Check all emails to see which one has LEUNG SHEUNG MAN
print(f"\n🔍 SEARCHING FOR 'LEUNG SHEUNG MAN' IN ALL EMAILS:")
emails_with_leung = Email.query.filter(
    (Email.alleged_subject.like('%LEUNG%')) |
    (Email.body.like('%LEUNG%'))
).all()

if emails_with_leung:
    for e in emails_with_leung:
        print(f"   - Email {e.id}: {e.subject[:50] if e.subject else 'No subject'}")
        print(f"     Alleged: {e.alleged_subject}")
        print(f"     Sender: {e.sender}")
else:
    print("   NO EMAILS FOUND WITH 'LEUNG' IN EMAIL TABLE")

# Check case profiles (alleged persons database)
print(f"\n👤 CASE PROFILES IN DATABASE (ALLEGED PERSONS):")
profiles = CaseProfile.query.all()
if profiles:
    for p in profiles:
        # CaseProfile doesn't have email_id, check by subject names
        print(f"   - ID {p.id}: {p.alleged_subject_en} {p.alleged_subject_cn}")
        print(f"     Company: {p.agent_company_broker}")
        print(f"     Case: {p.case_number}")
        if p.alleged_subject_en and 'LEUNG' in p.alleged_subject_en.upper():
            print(f"     ⚠️ THIS IS THE LEUNG PROFILE!")
else:
    print("   NO CASE PROFILES YET")

# Check if there are any attachments with similar filenames
print(f"\n� ALL ATTACHMENTS IN DATABASE:")
all_attachments = Attachment.query.all()
for att in all_attachments:
    size_mb = len(att.file_data) / (1024*1024) if att.file_data else 0
    print(f"   - ID {att.id}: {att.filename} (Email {att.email_id}, {size_mb:.1f} MB)")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Email 6 has {len(attachments)} attachment(s)")
print(f"Attachment 19 belongs to Email {att19.email_id if att19 else 'NOT FOUND'}")
print(f"'LEUNG' appears in {len(emails_with_leung)} email(s)")
print(f"Total case profiles: {len(profiles) if profiles else 0}")
print(f"Total attachments: {len(all_attachments)}")
print("=" * 80)
