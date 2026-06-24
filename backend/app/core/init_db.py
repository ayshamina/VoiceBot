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
    sample_entries = [
        {
            "question_en": "What courses does Bridgeon offer?",
            "answer_en": "Bridgeon offers professional, project-based training programs in AI, Data Science, Flutter, MERN Stack, Python Full Stack, and UI/UX Design.",
            "question_ml": "ബ്രിഡ്ജിയോൺ എന്തൊക്കെ കോഴ്സുകളാണ് നൽകുന്നത്?",
            "answer_ml": "ബ്രിഡ്ജിയോൺ AI, ഡാറ്റ സയൻസ്, ഫ്ലട്ടർ, MERN സ്റ്റാക്ക്, പൈത്തൺ ഫുൾ സ്റ്റാക്ക്, UI/UX ഡിസൈൻ തുടങ്ങിയ പ്രൊഫഷണൽ പ്രോജക്ട് അധിഷ്ഠിത കോഴ്സുകൾ നൽകുന്നു.",
            "category": "Course Info",
        },
        {
            "question_en": "How can I apply for admission?",
            "answer_en": "You can apply for admission by scheduling a free career counseling session. Please call us at +91 9539 50 30 30 or let me share the admission form link with you.",
            "question_ml": "ഞാൻ എങ്ങനെ അഡ്മിഷനായി അപേക്ഷിക്കണം?",
            "answer_ml": "ഒരു സൗജന്യ കരിയർ കൗൺസിലിംഗ് സെഷൻ ഷെഡ്യൂൾ ചെയ്തുകൊണ്ട് നിങ്ങൾക്ക് അഡ്മിഷനായി അപേക്ഷിക്കാം. ദയവായി +91 9539 50 30 30 എന്ന നമ്പറിൽ ബന്ധപ്പെടുക അല്ലെങ്കിൽ ഞാൻ നിങ്ങൾക്ക് അഡ്മിഷൻ ഫോം ലിങ്ക് അയച്ചുതരട്ടെയോ.",
            "category": "Admissions",
        },
        {
            "question_en": "What are the fees and payment options?",
            "answer_en": "Our fees vary depending on the course and payment plan you select. We offer flexible payment options including monthly EMIs, educational loans, scholarships, and a Pay After Placement option where you pay only after securing a job.",
            "question_ml": "കോഴ്സ് ഫീസും പെയ്‌മെന്റ് ഓപ്ഷനുകളും എന്തൊക്കെയാണ്?",
            "answer_ml": "ഓരോ കോഴ്‌സിന്റെയും ഫീസ് പ്ലാൻ അനുസരിച്ച് വ്യത്യസ്തമാണ്. പ്രതിമാസ EMI, വിദ്യാഭ്യാസ വായ്പകൾ, സ്കോളർഷിപ്പുകൾ, കൂടാതെ ജോലി ലഭിച്ച ശേഷം മാത്രം ഫീസ് അടയ്ക്കാവുന്ന 'പേ ആഫ്റ്റർ പ്ലേസ്‌മെന്റ്' എന്നീ ഫ്ലെക്സിബിൾ ഓപ്ഷനുകൾ ഞങ്ങൾ നൽകുന്നുണ്ട്.",
            "category": "Fees",
        },
        {
            "question_en": "Does Bridgeon provide internships, projects, or placement support?",
            "answer_en": "Yes, Bridgeon provides internship opportunities, practical projects, and 100% placement support. Our graduates get job placements with leading companies after completing their projects.",
            "question_ml": "ബ്രിഡ്ജിയോൺ ഇന്റേൺഷിപ്പുകൾ, പ്രോജക്റ്റുകൾ, അല്ലെങ്കിൽ പ്ലേസ്‌മെന്റ് സഹായം നൽകുന്നുണ്ടോ?",
            "answer_ml": "അതെ, ബ്രിഡ്ജിയോൺ കോഴ്സുകളുടെ ഭാഗമായി ഇന്റേൺഷിപ്പ് അവസരങ്ങളും പ്രായോഗിക പ്രോജക്റ്റുകളും 100% പ്ലേസ്‌മെന്റ് സഹായവും നൽകുന്നുണ്ട്. പ്രോജക്റ്റുകൾ പൂർത്തിയാക്കിയ ശേഷം പ്രമുഖ കമ്പനികളിൽ ഞങ്ങളുടെ വിദ്യാർത്ഥികൾക്ക് പ്ലേസ്‌മെന്റ് ലഭിക്കുന്നു.",
            "category": "Internships",
        },
        {
            "question_en": "Where is Bridgeon located and what are the office hours?",
            "answer_en": "Bridgeon is located at KINFRA Techno Industrial Park, Kakkanchery, Kozhikode, Kerala. Our office hours are Monday to Saturday from 9:00 AM to 6:00 PM.",
            "question_ml": "ബ്രിഡ്ജിയോൺ എവിടെയാണ് സ്ഥിതി ചെയ്യുന്നത്, ഓഫീസ് സമയം എപ്പോഴാണ്?",
            "answer_ml": "കോഴിക്കോട് കാക്കഞ്ചേരിയിലെ കിൻഫ്ര (KINFRA) ടെക്നോ ഇൻഡസ്ട്രിയൽ പാർക്കിലാണ് ബ്രിഡ്ജിയോൺ സ്ഥിതി ചെയ്യുന്നത്. ഞങ്ങളുടെ ഓഫീസ് സമയം തിങ്കൾ മുതൽ ശനി വരെ രാവിലെ 9:00 മുതൽ വൈകിട്ട് 6:00 വരെയാണ്.",
            "category": "General",
        },
    ]

    seeded_count = 0
    for entry_data in sample_entries:
        existing = db.query(Knowledge).filter(Knowledge.question_en == entry_data["question_en"]).first()
        if not existing:
            entry = Knowledge(**entry_data)
            db.add(entry)
            seeded_count += 1
            
    if seeded_count > 0:
        db.commit()
        print(f"[INIT] Seeded {seeded_count} missing FAQ entries into knowledge base.")
    else:
        print("[INIT] Knowledge base is already up to date. No new entries added.")

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
