"""
Script to update the active database settings and FAQ knowledge base entries
to match the new professional telecaller agent guidelines and new FAQs.
"""
import os
import sys
from pathlib import Path

# Add backend directory to path to allow imports
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal, init_db
from app.core.models import Knowledge, Setting
from app.core.rag import refresh_index

def main():
    print("[UpdateScript] Starting active database update...")
    db = SessionLocal()
    
    try:
        # 1. Update Greetings in Settings
        print("[UpdateScript] Updating greeting settings...")
        greetings = {
            "greeting_en": "Hello, thank you for calling Bridgeon. How may I assist you today?",
            "greeting_ml": "ഹലോ, ബ്രിഡ്ജിയോണിലേക്ക് വിളിച്ചതിന് നന്ദി. ഞാൻ ഇന്ന് നിങ്ങളെ എങ്ങനെയാണ് സഹായിക്കേണ്ടത്?"
        }
        
        for key, val in greetings.items():
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = val
                print(f"  - Updated existing setting '{key}'")
            else:
                setting = Setting(key=key, value=val)
                db.add(setting)
                print(f"  - Created new setting '{key}'")
        
        # 2. Replace FAQs in Knowledge Base
        print("[UpdateScript] Replacing FAQs in knowledge base...")
        # Delete old FAQs
        deleted_count = db.query(Knowledge).delete()
        print(f"  - Deleted {deleted_count} old FAQ entries.")
        
        # Insert new FAQs
        new_faqs = [
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
        
        for faq_data in new_faqs:
            entry = Knowledge(**faq_data)
            db.add(entry)
            print(f"  - Added FAQ: '{faq_data['question_en']}'")
            
        db.commit()
        print("[UpdateScript] Database commit successful.")
        
        # 3. Refresh RAG index
        print("[UpdateScript] Refreshing RAG index...")
        refresh_index(db)
        print("[UpdateScript] RAG index refreshed.")
        
    except Exception as e:
        db.rollback()
        print(f"[UpdateScript] ERROR during update: {e}", file=sys.stderr)
    finally:
        db.close()
        print("[UpdateScript] Database session closed.")

if __name__ == "__main__":
    main()
