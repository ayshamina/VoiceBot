"""
Database initialization script - Create all tables and load initial data.
Run this once before starting the application.
"""
from app.core.database import init_db, SessionLocal
from app.core.models import Knowledge, KnowledgeGap, Campaign
from app.core.settings_store import DEFAULT_SETTINGS, _ensure_defaults
from datetime import datetime, timezone


def init_sample_data():
    """Load sample knowledge base entries if database is empty."""
    db = SessionLocal()
    
    # Initialize default settings
    _ensure_defaults(db)
    
    # ── Knowledge Base ──────────────────────────────────────────────────────
    existing_count = db.query(Knowledge).count()
    if existing_count == 0:
        sample_entries = [
            {
                "question_en": "What is the course duration for MERN Stack?",
                "answer_en": "The MERN Stack program runs for 8 to 10 months and includes live projects, mock interviews, and placement support.",
                "question_ml": "MERN Stack കോഴ്സിന്റെ ദൈർഘ്യം എത്രമാണ്?",
                "answer_ml": "MERN Stack പ്രോഗ്രാം 8 മുതൽ 10 മാസം നീളുന്നു, ലൈവ് പ്രോജക്ടുകളും ഫീച്ചർ ഉള്ള പരിശീലനവും ഉൾപ്പെടുന്നു.",
                "category": "Course Info",
            },
            {
                "question_en": "How much is the admission fee?",
                "answer_en": "The admission fee varies by program; please contact admissions for the latest fee structure or request a callback.",
                "question_ml": "പ്രവേശന ഫീസ് എത്രയാണ്?",
                "answer_ml": "പ്രവേശന ഫീസ് പ്രോഗ്രാമിന്റെ അടിസ്ഥാനത്തിൽ വ്യത്യാസപ്പെടുന്നു; ഏറ്റവും പുതിയ വിവരങ്ങൾക്ക് അഡ്മിഷൻ ടീമുമായി ബന്ധപ്പെടുക.",
                "category": "Fees",
            },
            {
                "question_en": "Do you offer placement assistance?",
                "answer_en": "Yes, we provide 100% placement assistance including resume building, interview preparation, and job placements with leading companies.",
                "question_ml": "നിങ്ങൾ നിയമനം സഹായം നൽകുന്നുണ്ടോ?",
                "answer_ml": "അതെ, ഞാൻ 100% നിയമനം സഹായം നൽകുന്നു, റെസ്യുമെ നിർമ്മാണം, ഇന്റർവ്യൂ പ്രസ്തുതി, കൂടാതെ നിയമനം.",
                "category": "Placement",
            },
        ]
        for entry_data in sample_entries:
            entry = Knowledge(**entry_data)
            db.add(entry)
        db.commit()
        print(f"[INIT] Loaded {len(sample_entries)} sample FAQ entries into knowledge base.")
    else:
        print(f"[INIT] Knowledge base already has {existing_count} entries. Skipping.")

    # ── Knowledge Gaps (seed demo data) ────────────────────────────────────
    gap_count = db.query(KnowledgeGap).count()
    if gap_count == 0:
        sample_gaps = [
            {
                "question": "Do you offer weekend batches for Flutter course?",
                "frequency": 14,
                "category": "Course Info",
            },
            {
                "question": "Is food and accommodation provided at Kozhikode campus?",
                "frequency": 9,
                "category": "General",
            },
            {
                "question": "Can I pay the fees in monthly installments after placement?",
                "frequency": 7,
                "category": "Fees",
            },
            {
                "question": "Is there any age limit to join MERN stack?",
                "frequency": 4,
                "category": "Admissions",
            },
        ]
        for gap_data in sample_gaps:
            gap = KnowledgeGap(**gap_data)
            db.add(gap)
        db.commit()
        print(f"[INIT] Seeded {len(sample_gaps)} sample knowledge gaps.")
    else:
        print(f"[INIT] Knowledge gaps table already has {gap_count} entries. Skipping.")

    # ── Campaigns (seed demo data) ─────────────────────────────────────────
    campaign_count = db.query(Campaign).count()
    if campaign_count == 0:
        sample_campaigns = [
            {
                "name": "June Batch Follow-Up",
                "channel": "voice",
                "script": "Hello, this is Bridgeon Skillversity calling to follow up on your enquiry for the MERN Stack development course...",
                "schedule_time": "2026-06-25T10:00",
                "status": "Running",
                "retry_attempts": 3,
                "consent_required": True,
                "dnd_compliance": True,
                "contacted": 48,
                "answered": 32,
                "converted": 7,
            },
            {
                "name": "Data Science Enquiry Leads",
                "channel": "whatsapp",
                "script": "Hi! We have scheduled a demo batch for our Data Science course next Monday. Reply YES to register.",
                "schedule_time": "2026-06-28T14:30",
                "status": "Scheduled",
                "retry_attempts": 1,
                "consent_required": True,
                "dnd_compliance": True,
                "contacted": 0,
                "answered": 0,
                "converted": 0,
            },
            {
                "name": "May Outreach — Flutter",
                "channel": "voice",
                "script": "Hello, this is Bridgeon Skillversity calling to follow up on our Flutter app development program admissions...",
                "schedule_time": "2026-05-15T09:00",
                "status": "Completed",
                "retry_attempts": 3,
                "consent_required": True,
                "dnd_compliance": True,
                "contacted": 120,
                "answered": 87,
                "converted": 23,
            },
        ]
        for c_data in sample_campaigns:
            campaign = Campaign(**c_data)
            db.add(campaign)
        db.commit()
        print(f"[INIT] Seeded {len(sample_campaigns)} sample campaigns.")
    else:
        print(f"[INIT] Campaigns table already has {campaign_count} entries. Skipping.")

    db.close()


if __name__ == "__main__":
    print("[INIT] Starting database initialization...")
    init_db()
    init_sample_data()
    print("[INIT] Database initialization complete!")
