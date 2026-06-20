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
        # Original Seed Data
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
        # Comprehensive Course Guide Seed Data
        {
            "question_en": "What is Bridgeon Skillversity?",
            "answer_en": "Bridgeon Skillversity (formerly Bridgeon Solutions) is Kerala's No.1 Software Training Institute, operating as a practical, job-oriented IT and creative training bootcamp focused on mentorship, live projects, and placements. Over 400 students have been placed since its founding in 2022.",
            "question_ml": "എന്താണ് ബ്രിഡ്ജിയോൺ സ്കിൽവേഴ്സിറ്റി?",
            "answer_ml": "മെന്റർഷിപ്പ്, ലൈവ് പ്രോജക്റ്റുകൾ, പ്ലേസ്‌മെന്റുകൾ എന്നിവയിൽ ശ്രദ്ധ കേന്ദ്രീകരിക്കുന്ന പ്രായോഗികവും ജോലിധിഷ്ഠിതവുമായ ഐടി, ക്രിയേറ്റീവ് ട്രെയിനിംഗ് ബൂട്ട്ക്യാമ്പാണ് ബ്രിഡ്ജിയോൺ സ്കിൽവേഴ്സിറ്റി. 2022-ൽ സ്ഥാപിതമായതു മുതൽ 400-ലധികം വിദ്യാർത്ഥികൾക്ക് ഇവിടെനിന്നും വിവിധ കമ്പനികളിലായി ജോലി ലഭിച്ചിട്ടുണ്ട്.",
            "category": "General",
        },
        {
            "question_en": "Where is Bridgeon located?",
            "answer_en": "Bridgeon has two hubs in Calicut: 1) Main Hub (HQ) at Neospace, KINFRA Techno Industrial Park, Kakkanchery, Chelambra, Kozhikode, Kerala - 673635. 2) Pantheeramkavu Hub at 1st Floor, Thappy's Arcade, NH Bypass Road, Pantheeramkavu, Kozhikode, Kerala - 673019. Phone: +91 9539 50 30 30.",
            "question_ml": "ബ്രിഡ്ജിയോൺ എവിടെയാണ് സ്ഥിതി ചെയ്യുന്നത്?",
            "answer_ml": "ബ്രിഡ്ജിയോണിന് കോഴിക്കോട് രണ്ട് ശാഖകളുണ്ട്: 1) മെയിൻ ഹബ് (HQ): നിയോസ്പേസ്, കിൻഫ്ര ടെക്നോ ഇൻഡസ്ട്രിയൽ പാർക്ക്, കാക്കഞ്ചേരി, കോഴിക്കോട്, കേരളം - 673635. 2) പന്തീരാങ്കാവ് ഹബ്: ഫസ്റ്റ് ഫ്ലോർ, തപ്പീസ് ആർക്കേഡ്, എൻ എച്ച് ബൈപാസ് റോഡ്, പന്തീരാങ്കാവ്, കേരളം - 673019.",
            "category": "General",
        },
        {
            "question_en": "What courses are offered at Bridgeon Tech School?",
            "answer_en": "Bridgeon Tech School offers 6-10 months bootcamps in offline and online modes for: MERN Stack, MEAN Stack, Python Full Stack (Django + React), Flutter/Dart (Mobile App Dev), Java Spring Boot, .NET Core, Golang, DevOps, Data Analytics, Cyber Security, and Software Testing.",
            "question_ml": "ബ്രിഡ്ജിയോൺ ടെക് സ്കൂളിൽ എന്തൊക്കെ കോഴ്സുകൾ ഉണ്ട്?",
            "answer_ml": "ബ്രിഡ്ജിയോൺ ടെക് സ്കൂൾ 6-10 മാസം ദൈർഘ്യമുള്ള ഓഫ്‌ലൈൻ/ഓൺലൈൻ കോഴ്‌സുകൾ നൽകുന്നു: MERN സ്റ്റാക്ക്, MEAN സ്റ്റാക്ക്, പൈത്തൺ ഫുൾ സ്റ്റാക്ക്, ഫ്ലട്ടർ/ഡാർട്ട് മൊബൈൽ ആപ്പ് ഡെവലപ്‌മെന്റ്, ജാവ സ്പ്രിംഗ് ബൂട്ട്, .NET, ഗോലാംഗ്, ഡെവ്ഓപ്സ്, ഡാറ്റ അനലിറ്റിക്സ്, സൈബർ സെക്യൂരിറ്റി, സോഫ്റ്റ്‌വെയർ ടെസ്റ്റിംഗ്.",
            "category": "Course Info",
        },
        {
            "question_en": "What courses are offered at Bridgeon Media School?",
            "answer_en": "Bridgeon Media School offers creative courses with professional studio facilities: Advanced Photography, Advanced Videography, Advanced Video Editing, Digital Marketing, and Graphic Designing. Contact +91 9037 56 3030 or email media@bridgeon.in.",
            "question_ml": "ബ്രിഡ്ജിയോൺ മീഡിയ സ്കൂളിൽ എന്തൊക്കെ കോഴ്സുകൾ ഉണ്ട്?",
            "answer_ml": "പ്രൊഫഷണൽ സ്റ്റുഡിയോ സൗകര്യങ്ങളുള്ള ക്രിയേറ്റീവ് കോഴ്‌സുകൾ ബ്രിഡ്ജിയോൺ മീഡിയ സ്കൂൾ നൽകുന്നു: അഡ്വാൻസ്ഡ് ഫോട്ടോഗ്രാഫി, അഡ്വാൻസ്ഡ് വീഡിയോഗ്രാഫി, അഡ്വാൻസ്ഡ് വീഡിയോ എഡിറ്റിംഗ്, ഡിജിറ്റൽ മാർക്കറ്റിംഗ്, ഗ്രാഫിക് ഡിസൈനിംഗ്. ഫോൺ: +91 9037 56 3030.",
            "category": "Course Info",
        },
        {
            "question_en": "What is the Skill First Degree Program?",
            "answer_en": "The Skill First Degree Program is a 2-3 year model where you earn a UGC-recognized university degree while simultaneously gaining job-ready practical skills. You can earn while you learn and graduate with both a degree and corporate experience.",
            "question_ml": "എന്താണ് സ്കിൽ ഫസ്റ്റ് ഡിഗ്രി പ്രോഗ്രാം?",
            "answer_ml": "യുജിസി അംഗീകൃത സർവ്വകലാശാലാ ബിരുദം നേടുന്നതിനൊപ്പം തൊഴിൽ സജ്ജമായ പ്രായോഗിക നൈപുണ്യങ്ങൾ നേടാൻ സഹായിക്കുന്ന 2-3 വർഷത്തെ പ്രോഗ്രാമാണിത്. പഠനത്തോടൊപ്പം സമ്പാദിക്കാനും ബിരുദവും അനുഭവപരിചയവും നേടി ബിരുദധാരിയാകാനും ഇത് സഹായിക്കുന്നു.",
            "category": "Course Info",
        },
        {
            "question_en": "What is the fee structure and payment options?",
            "answer_en": "Bridgeon does not publish specific fee amounts publicly. Fees are discussed during a free counseling session. Payment options include: Pay After Placement (pay only after getting a job), flexible monthly EMIs, Educational Loans, Scholarships, and upfront payment discounts.",
            "question_ml": "കോഴ്സ് ഫീസും പെയ്‌മെന്റ് ഓപ്ഷനുകളും എന്തൊക്കെയാണ്?",
            "answer_ml": "ബ്രിഡ്ജിയോൺ ഫീസ് വിവരങ്ങൾ പരസ്യമായി നൽകുന്നില്ല. കൗൺസിലിംഗ് സമയത്ത് ഇത് വ്യക്തമാക്കും. പെയ്‌മെന്റ് ഓപ്ഷനുകൾ: പേ ആഫ്റ്റർ പ്ലേസ്‌മെന്റ് (ജോലി ലഭിച്ച ശേഷം മാത്രം ഫീസ് അടയ്ക്കുക), പ്രതിമാസ EMI, വിദ്യാഭ്യാസ വായ്പകൾ, സ്കോളർഷിപ്പുകൾ, ഒറ്റത്തവണ പേയ്‌മെന്റ് ഡിസ്‌കൗണ്ടുകൾ.",
            "category": "Fees",
        },
        {
            "question_en": "How long are the courses at Bridgeon?",
            "answer_en": "Tech School Bootcamps run for 6-10 months (including a 2-4 months project phase). Creative courses take 3-6 months. The Skill First Degree Program takes 2-3 years, and general certification tracks are 3-6 months. The average timeline from enrollment to placement is 4-8 months.",
            "question_ml": "കോഴ്സുകളുടെ ദൈർഘ്യം എത്രയാണ്?",
            "answer_ml": "ടെക് സ്കൂൾ ബൂട്ട്ക്യാമ്പ് 6-10 മാസവും (ഇതിൽ 2-4 മാസം ഇന്റേൺഷിപ്പ്/പ്രോജക്റ്റ് ഉൾപ്പെടുന്നു), മീഡിയ സ്കൂൾ കോഴ്സുകൾ 3-6 മാസവുമാണ്. സ്കിൽ ഫസ്റ്റ് ഡിഗ്രി പ്രോഗ്രാം 2-3 വർഷവും സർട്ടിഫിക്കേഷൻ കോഴ്സുകൾ 3-6 മാസവുമാണ്.",
            "category": "Course Info",
        },
        {
            "question_en": "What are the class timings and structure at Bridgeon?",
            "answer_en": "Bridgeon does not publish fixed batch timings publicly. Timings depend on morning, evening, or weekend slots. It features a self-paced learning model with 24/7 mentor availability and weekly project reviews by industry professionals.",
            "question_ml": "ക്ലാസ് സമയങ്ങളും പഠന രീതിയും എങ്ങനെയാണ്?",
            "answer_ml": "ക്ലാസ് സമയം ഓരോ ബാച്ചിനും (മോണിംഗ്/ഈവനിംഗ്/വീക്കെൻഡ്) ശാഖയ്ക്കും അനുസരിച്ച് വ്യത്യാസപ്പെടുന്നു. 24/7 മെന്റർ പിന്തുണയോടു കൂടിയ സ്വയം പഠന രീതിയും പ്രൊഫഷണലുകൾ നടത്തുന്ന പ്രതിവാര റിവ്യൂകളും ഇതിന്റെ പ്രത്യേകതയാണ്.",
            "category": "General",
        },
        {
            "question_en": "What placement support does Bridgeon provide?",
            "answer_en": "Bridgeon provides 100% placement support with a 90%+ placement rate and 150+ hiring partners. Support includes professional resume workshops, mock interviews, LinkedIn optimization, direct company referrals, and optional Pay After Placement plans.",
            "question_ml": "പ്ലേസ്‌മെന്റ് സഹായങ്ങൾ എങ്ങനെയാണ് നൽകുന്നത്?",
            "answer_ml": "ബ്രിഡ്ജിയോൺ 90%-ലധികം വിജയശതമാനത്തോടെ 100% പ്ലേസ്‌മെന്റ് സഹായം നൽകുന്നു. റെസ്യൂമെ നിർമ്മാണം, മോക്ക് ഇന്റർവ്യൂകൾ, ലിങ്ക്ഡ്ഇൻ പ്രൊഫൈൽ ബിൽഡിംഗ്, ഡയറക്റ്റ് റഫറലുകൾ എന്നിവ ഇതിൽ ഉൾപ്പെടുന്നു.",
            "category": "Placement",
        },
        {
            "question_en": "Who is eligible to join Bridgeon courses?",
            "answer_en": "Bridgeon courses are open to anyone with a desire to switch to IT—no prior IT background is required. 70% of placed students had zero prior IT experience. Open to Plus Two/12th pass, Degree/Diploma holders, PG graduates, and working professionals.",
            "question_ml": "ബ്രിഡ്ജിയോൺ കോഴ്സുകളിൽ ചേരാനുള്ള യോഗ്യത എന്താണ്?",
            "answer_ml": "ഐടി പശ്ചാത്തലമില്ലാത്തവർക്കും കോഴ്‌സുകളിൽ ചേരാം. പ്ലേസ്‌മെന്റ് ലഭിച്ച 70% പേർക്കും മുൻപരിചയം ഉണ്ടായിരുന്നില്ല. പ്ലസ് ടു കഴിഞ്ഞവർ, ഡിഗ്രി/ഡിപ്ലോമക്കാർ, പിജി കഴിഞ്ഞവർ, ജോലി മാറാൻ ആഗ്രഹിക്കുന്നവർ എന്നിവർക്കെല്ലാം ചേരാവുന്നതാണ്.",
            "category": "General",
        },
        {
            "question_en": "What is the enrollment process at Bridgeon?",
            "answer_en": "To enroll: 1) Call +91 9539 50 30 30 to schedule a free counseling session. 2) Attend the session to discuss your career goals and select your course. 3) Confirm your fee structure and payment options. 4) Complete enrollment to receive your joining kit.",
            "question_ml": "ബ്രിഡ്ജിയോണിൽ എങ്ങനെ അഡ്മിഷൻ നേടാം?",
            "answer_ml": "1) +91 9539 50 30 30 എന്ന നമ്പറിൽ വിളിച്ച് കൗൺസിലിംഗ് ഷെഡ്യൂൾ ചെയ്യുക. 2) കൗൺസിലിംഗിൽ പങ്കെടുത്ത് നിങ്ങളുടെ കോഴ്‌സ് തിരഞ്ഞെടുക്കുക. 3) ഫീസ് ഘടനയും പെയ്‌മെന്റ് ഓപ്ഷനും ഉറപ്പുവരുത്തുക. 4) എൻറോൾമെന്റ് പൂർത്തിയാക്കി ജോയിനിംഗ് കിറ്റ് കൈപ്പറ്റുക.",
            "category": "General",
        },
        {
            "question_en": "What are Bridgeon's contact details and social media handles?",
            "answer_en": "Contact Tech School: +91 9539 50 30 30, Media School: +91 9037 56 3030. Email: info@bridgeon.in. Follow on Instagram: @bridgeon.techschool or @bridgeon_mediaschool. LinkedIn: linkedin.com/company/bridgeon-tech-school. YouTube: youtube.com/@bridgeon.",
            "question_ml": "ബ്രിഡ്ജിയോണിന്റെ ഫോൺ നമ്പറും സോഷ്യൽ മീഡിയ വിലാസങ്ങളും എന്തൊക്കെയാണ്?",
            "answer_ml": "ടെക് സ്കൂൾ: +91 9539 50 30 30. മീഡിയ സ്കൂൾ: +91 9037 56 3030. ഇമെയിൽ: info@bridgeon.in. ഇൻസ്റ്റാഗ്രാം: @bridgeon.techschool അല്ലെങ്കിൽ @bridgeon_mediaschool. ലിങ്ക്ഡ്ഇൻ: linkedin.com/company/bridgeon-tech-school.",
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
