import re
import difflib
from typing import Dict, List, Optional, Tuple

# Full curated multi-lingual dataset provided for RAVISN
RAVISN_QA_DATA: List[Dict[str, str]] = [
    # English Greetings & Basics
    {"q": "Assalamualaikum", "a": "Wa Alaikum Assalam! How can we help you?", "lang": "roman_urdu", "cat": "greeting"},
    {"q": "Hello", "a": "Hello! How can RAVISN help you today?", "lang": "english", "cat": "greeting"},
    {"q": "Hi", "a": "Hi! How can we assist you?", "lang": "english", "cat": "greeting"},
    {"q": "Hey", "a": "Hey! How can we help?", "lang": "english", "cat": "greeting"},
    {"q": "Good morning", "a": "Good morning! How can we help you today?", "lang": "english", "cat": "greeting"},
    {"q": "Good afternoon", "a": "Good afternoon! How can we assist you?", "lang": "english", "cat": "greeting"},
    {"q": "Good evening", "a": "Good evening! How can we help?", "lang": "english", "cat": "greeting"},
    {"q": "How are you?", "a": "We’re doing great, thank you! How can we help you?", "lang": "english", "cat": "greeting"},
    {"q": "Who are you?", "a": "We are RAVISN, an AI automation agency.", "lang": "english", "cat": "identity"},
    {"q": "What is RAVISN?", "a": "RAVISN provides AI automation solutions for businesses — AI Automation That Grows Your Business, On Autopilot.", "lang": "english", "cat": "identity"},
    {"q": "What do you do?", "a": "We help businesses automate customer support, sales, leads, workflows, and more.", "lang": "english", "cat": "services"},
    {"q": "Are you a real person?", "a": "I’m RAVISN’s AI assistant. I can help with information about our services.", "lang": "english", "cat": "identity"},
    {"q": "Are you AI?", "a": "Yes, I’m an AI assistant for RAVISN.", "lang": "english", "cat": "identity"},
    {"q": "Can I talk to a human?", "a": "Yes. Please contact the RAVISN team on WhatsApp (+1 564-222-6889) for human assistance.", "lang": "english", "cat": "support"},
    {"q": "Can you help me?", "a": "Yes, of course. Tell me what you need.", "lang": "english", "cat": "general"},
    {"q": "Do you make websites?", "a": "Our main focus is AI automation and custom AI solutions. Please share your requirement.", "lang": "english", "cat": "services"},
    {"q": "Do you make apps?", "a": "We can discuss custom AI and automation solutions based on your requirement.", "lang": "english", "cat": "services"},
    {"q": "Can you build a chatbot for my business?", "a": "Yes, we can build an AI chatbot for your business.", "lang": "english", "cat": "services"},
    {"q": "Can I use it on WhatsApp?", "a": "Yes, WhatsApp AI automation is available.", "lang": "english", "cat": "services"},
    {"q": "Can I use it on my website?", "a": "Yes, AI customer support can be integrated with a website.", "lang": "english", "cat": "services"},
    {"q": "Can it answer customers automatically?", "a": "Yes, an AI agent can automatically handle customer questions 24/7.", "lang": "english", "cat": "features"},
    {"q": "Can it work 24/7?", "a": "Yes, AI customer support can operate around the clock.", "lang": "english", "cat": "features"},
    {"q": "Can it understand my business?", "a": "Yes, you can provide business knowledge to guide the AI agent.", "lang": "english", "cat": "features"},
    {"q": "Can I upload a PDF?", "a": "Yes, your business documents and PDFs can be added to the AI knowledge base.", "lang": "english", "cat": "features"},
    {"q": "Can I add my company information?", "a": "Yes, company information can be added to the AI knowledge base.", "lang": "english", "cat": "features"},
    {"q": "What if the answer is not in my knowledge?", "a": "The configured AI fallback will politely offer human assistance or answer safely without hallucinations.", "lang": "english", "cat": "features"},
    {"q": "Can it sell products?", "a": "Yes, AI can assist with customer conversations and sales workflows.", "lang": "english", "cat": "features"},
    {"q": "Can it collect leads?", "a": "Yes, lead collection and qualification can be automated.", "lang": "english", "cat": "features"},
    {"q": "Can it book appointments?", "a": "Yes, appointment booking automation can be configured.", "lang": "english", "cat": "features"},
    {"q": "Can it send follow-ups?", "a": "Yes, follow-up workflows can be automated.", "lang": "english", "cat": "features"},
    {"q": "Can it connect to CRM?", "a": "Yes, CRM automation and integrations can be connected based on your system.", "lang": "english", "cat": "features"},
    {"q": "Can it handle customer complaints?", "a": "Yes, AI can handle common support conversations and route complex cases to your human team.", "lang": "english", "cat": "features"},
    {"q": "Is there a free plan?", "a": "Please contact RAVISN for the latest available plans and options. We offer a free consultation for every new client.", "lang": "english", "cat": "pricing"},
    {"q": "Do you offer a demo?", "a": "Yes, you can contact RAVISN to discuss a demo. You are also talking to one right now!", "lang": "english", "cat": "demo"},
    {"q": "How do I start?", "a": "Tell us about your business and automation requirements, and the RAVISN team can guide you. Book a free consultation on WhatsApp!", "lang": "english", "cat": "onboarding"},
    {"q": "Do you work with small businesses?", "a": "Yes, solutions can be customized for different business sizes.", "lang": "english", "cat": "industries"},
    {"q": "Do you work with large companies?", "a": "Yes, custom automation can be designed for larger operations.", "lang": "english", "cat": "industries"},
    {"q": "I want an AI agent", "a": "Sure. Tell us what you want the AI agent to do.", "lang": "english", "cat": "services"},
    {"q": "I want WhatsApp automation", "a": "Sure. Share your WhatsApp automation requirements with the RAVISN team.", "lang": "english", "cat": "services"},
    {"q": "I want a voice bot", "a": "Yes, RAVISN offers AI voice agent solutions for inbound and outbound calls.", "lang": "english", "cat": "services"},
    {"q": "I want a sales bot", "a": "Yes, we can build an AI sales agent for your business.", "lang": "english", "cat": "services"},
    {"q": "I want customer support AI", "a": "Yes, we build 24/7 AI-powered customer support solutions.", "lang": "english", "cat": "services"},
    {"q": "I want lead generation automation", "a": "Yes, lead capture, qualification, and follow-up can be automated.", "lang": "english", "cat": "services"},
    {"q": "Tell me a joke", "a": "Sure! Why did the chatbot get promoted? Because it always had the right response!", "lang": "english", "cat": "chitchat"},
    {"q": "What is your phone number?", "a": "Our official WhatsApp and phone contact is +1 (564) 222-6889.", "lang": "english", "cat": "contact"},
    {"q": "What is your email?", "a": "You can contact RAVISN by email at Ravisn.uk@gmail.com.", "lang": "english", "cat": "contact"},
    {"q": "What is your website?", "a": "RAVISN's official website is ravisn.com.", "lang": "english", "cat": "contact"},
    {"q": "Are you on Instagram?", "a": "Yes! Our official Instagram handle is @ravisnofficial.", "lang": "english", "cat": "contact"},
    {"q": "Where are you located?", "a": "Our office is at 41, McLeod Road, Lahore, and our US office is at 312 W 2ND ST 1992 CASPER, WY 82601.", "lang": "english", "cat": "contact"},
    {"q": "How much does it cost?", "a": "Pricing depends on your business needs and project scope since every solution is custom-built. Our team shares a tailored quote after a free consultation on WhatsApp.", "lang": "english", "cat": "pricing"},
    {"q": "What is your price?", "a": "We do not have fixed pricing because every business is unique. We provide a custom quote after a free consultation call.", "lang": "english", "cat": "pricing"},
    {"q": "Can you help my real estate business?", "a": "Yes! We build custom AI automation for real estate (24/7 lead qualification, WhatsApp follow-ups, CRM sync, and voice booking agents).", "lang": "english", "cat": "industries"},
    {"q": "Do you work with real estate?", "a": "Yes, RAVISN provides specialized automation solutions for real estate businesses.", "lang": "english", "cat": "industries"},
    {"q": "Can you help my restaurant?", "a": "Yes, AI automation can support restaurants with customer inquiries, bookings, orders, and promotions.", "lang": "english", "cat": "industries"},
    {"q": "Can you help my clinic?", "a": "Yes, we provide AI automation for clinics, aesthetics, and healthcare for 24/7 appointment scheduling and customer support.", "lang": "english", "cat": "industries"},
    {"q": "Can you help my ecommerce business?", "a": "Yes, AI automation can support e-commerce customer service, order tracking, sales, and abandoned cart recovery.", "lang": "english", "cat": "industries"},
    {"q": "Can you help my HVAC business?", "a": "Yes, HVAC and home-service businesses can automate inbound emergency calls, quote requests, and dispatching.", "lang": "english", "cat": "industries"},
    {"q": "What is included in the Basic package?", "a": "The Basic Package includes Website AI Chatbot setup, Lead Capture Automation, WhatsApp Integration, Appointment Booking, Basic CRM Integration, Free Consultation, 30 Days Support, and Basic Training.", "lang": "english", "cat": "packages"},
    {"q": "What is in the All-in-One package?", "a": "The All-in-One Solution (Recommended) includes everything in Basic plus AI Voice Agent, CRM Automation, Email & SMS Automation, Lead Qualification AI, Workflow Automation, Monthly Performance Report, Strategy Session, 60 Days Support, and Workflow Optimization.", "lang": "english", "cat": "packages"},
    {"q": "What is in the Premium package?", "a": "The Premium Package includes everything in All-in-One plus Custom AI Agent Development, Multi-Channel Automation (WhatsApp + Voice + Email AI), Advanced CRM & API Integrations, Dedicated Account Manager, Priority Support, Growth Consultation, and 90 Days Premium Support.", "lang": "english", "cat": "packages"},
    {"q": "How long does setup take?", "a": "Most AI automation projects are delivered within 1–4 weeks, depending on project scope.", "lang": "english", "cat": "timeline"},
    {"q": "How many projects has RAVISN completed?", "a": "RAVISN has completed 300+ projects with 500+ reviews and 98% happy clients.", "lang": "english", "cat": "about"},

    # Roman Urdu Q&As
    {"q": "Assalam o Alaikum", "a": "Wa Alaikum Assalam! RAVISN mein khush aamdeed. Batayein hum kis tarah help kar sakte hain?", "lang": "roman_urdu", "cat": "greeting"},
    {"q": "Salam", "a": "Wa Alaikum Assalam! Kaise help kar sakte hain?", "lang": "roman_urdu", "cat": "greeting"},
    {"q": "Kese ho?", "a": "Alhamdulillah, theek! Aap batayein kis cheez mein help chahiye?", "lang": "roman_urdu", "cat": "greeting"},
    {"q": "Aap kon ho?", "a": "Main RAVISN ka AI assistant hoon.", "lang": "roman_urdu", "cat": "identity"},
    {"q": "RAVISN kya hai?", "a": "RAVISN AI automation agency hai jo businesses ko automation solutions deti hai.", "lang": "roman_urdu", "cat": "identity"},
    {"q": "Aap kya karte ho?", "a": "Hum AI chatbot, voice agent, WhatsApp automation, lead automation aur custom AI solutions provide karte hain.", "lang": "roman_urdu", "cat": "services"},
    {"q": "Aapka email kya hai?", "a": "Aap hum se email par contact kar sakte hain: Ravisn.uk@gmail.com.", "lang": "roman_urdu", "cat": "contact"},
    {"q": "Aapka number kya hai?", "a": "RAVISN ka official WhatsApp number +1 (564) 222-6889 hai.", "lang": "roman_urdu", "cat": "contact"},
    {"q": "Aap kahan located hain?", "a": "RAVISN ka office 41, McLeod Road, Lahore mein hai aur hamara US office Casper, WY mein hai.", "lang": "roman_urdu", "cat": "contact"},
    {"q": "Aapki website kya hai?", "a": "Hamari official website ravisn.com hai.", "lang": "roman_urdu", "cat": "contact"},
    {"q": "Price kya hai?", "a": "Pricing aapki requirements par depend karti hai. Hum free consultation ke baad custom quote share karte hain.", "lang": "roman_urdu", "cat": "pricing"},
    {"q": "Iski price kitni hai?", "a": "Price business needs aur project scope par depend karti hai. Free consultation ke baad custom quote milta hai.", "lang": "roman_urdu", "cat": "pricing"},
    {"q": "Aapki price kya hai?", "a": "Fixed price nahi hai. Har business ke liye custom quote diya jata hai.", "lang": "roman_urdu", "cat": "pricing"},
    {"q": "Demo mil sakta hai?", "a": "Ji haan! Aap abhi RAVISN WhatsApp assistant se chat kar rahe hain. Custom demo consultation ke baad arrange ho sakta hai.", "lang": "roman_urdu", "cat": "demo"},
    {"q": "Start kaise karoon?", "a": "WhatsApp par free consultation book karein, apni business needs share karein, aur hamari team aap ko guide karegi.", "lang": "roman_urdu", "cat": "onboarding"},
    {"q": "Real estate ke liye AI hai?", "a": "Ji haan! Real estate ke liye lead qualification, WhatsApp follow-ups, aur 24/7 AI chat/voice agents automate ho sakte hain.", "lang": "roman_urdu", "cat": "industries"},
    {"q": "Restaurant ke liye AI ban sakta hai?", "a": "Ji haan, restaurant ke customer questions, bookings, leads aur workflows automate ho sakte hain.", "lang": "roman_urdu", "cat": "industries"},
    {"q": "Clinic ke liye AI hai?", "a": "Ji haan, customer support aur appointment workflows ke liye AI solution banaya ja sakta hai.", "lang": "roman_urdu", "cat": "industries"},
    {"q": "Online store ke liye AI hai?", "a": "Ji haan, ecommerce customer support, sales aur workflows automate kiye ja sakte hain.", "lang": "roman_urdu", "cat": "industries"},
    {"q": "Basic package mein kya included hai?", "a": "Basic package mein website AI chatbot setup, lead capture, WhatsApp integration, appointment booking, basic CRM integration, consultation, 30 days support aur training shamil hai.", "lang": "roman_urdu", "cat": "packages"},
    {"q": "All-in-One package mein kya hai?", "a": "All-in-One solution mein Basic ke sath AI voice agent, CRM automation, email/SMS automation, lead qualification AI, workflow automation, 60 days support shamil hai.", "lang": "roman_urdu", "cat": "packages"},
    {"q": "Premium package mein kya included hai?", "a": "Premium package mein custom AI agent development, multi-channel automation (WhatsApp + Voice + Email), advanced CRM/API integrations, dedicated account manager, aur 90 days premium support shamil hai.", "lang": "roman_urdu", "cat": "packages"},
    {"q": "Setup mein kitna time lagta hai?", "a": "Aksar AI automation projects 1–4 weeks mein deliver ho jate hain.", "lang": "roman_urdu", "cat": "timeline"},
    {"q": "Kya support milti hai?", "a": "Ji haan. Delivery ke baad ongoing support, monitoring aur optimization milti hai.", "lang": "roman_urdu", "cat": "support"},
    {"q": "Kya aap WhatsApp automate karte hain?", "a": "Ji haan. Hum WhatsApp Business par customer chats, leads, appointments aur support automate karte hain.", "lang": "roman_urdu", "cat": "services"},
    {"q": "Kya aap AI chatbot banate hain?", "a": "Ji haan. Hum 24/7 AI chatbots banate hain jo questions, leads aur customer engagement handle karte hain.", "lang": "roman_urdu", "cat": "services"},
    {"q": "Kya aap AI voice agent banate hain?", "a": "Ji haan. AI voice agents inbound/outbound calls, bookings aur follow-ups automate kar sakte hain.", "lang": "roman_urdu", "cat": "services"},
    {"q": "Kya aap CRM automate kar sakte hain?", "a": "Ji haan. CRM ko AI workflows ke sath connect karke leads aur follow-ups automate kiye ja sakte hain.", "lang": "roman_urdu", "cat": "services"},

    # Urdu Nastaliq Q&As
    {"q": "السلام علیکم", "a": "وعلیکم السلام! RAVISN میں خوش آمدید۔ بتائیں ہم آپ کی کیسے مدد کر سکتے ہیں؟", "lang": "urdu_nastaliq", "cat": "greeting"},
    {"q": "سلام", "a": "وعلیکم السلام! بتائیں آپ کی کیسے مدد کریں؟", "lang": "urdu_nastaliq", "cat": "greeting"},
    {"q": "ہیلو", "a": "ہیلو! RAVISN میں خوش آمدید۔ کیسے مدد کریں؟", "lang": "urdu_nastaliq", "cat": "greeting"},
    {"q": "آپ کیسے ہیں؟", "a": "الحمدللہ ٹھیک! بتائیں آپ کو کس چیز میں مدد چاہیے؟", "lang": "urdu_nastaliq", "cat": "greeting"},
    {"q": "آپ کون ہیں؟", "a": "میں RAVISN کا AI اسسٹنٹ ہوں۔", "lang": "urdu_nastaliq", "cat": "identity"},
    {"q": "RAVISN کیا ہے؟", "a": "RAVISN ایک AI آٹومیشن ایجنسی ہے جو کاروباروں کو آٹومیشن سلوشنز فراہم کرتی ہے۔", "lang": "urdu_nastaliq", "cat": "identity"},
    {"q": "آپ کیا کرتے ہیں؟", "a": "ہم AI چیٹ بوٹس، وائس ایجنٹس، واٹس ایپ آٹومیشن، لیڈ آٹومیشن اور کسٹم AI سلوشنز فراہم کرتے ہیں۔", "lang": "urdu_nastaliq", "cat": "services"},
    {"q": "آپ کا ای میل کیا ہے؟", "a": "آپ ہم سے Ravisn.uk@gmail.com پر رابطہ کر سکتے ہیں۔", "lang": "urdu_nastaliq", "cat": "contact"},
    {"q": "آپ کا نمبر کیا ہے؟", "a": "ہمارا آفیشل واٹس ایپ نمبر 6889-222 (564) 1+ ہے۔", "lang": "urdu_nastaliq", "cat": "contact"},
    {"q": "آپ کہاں موجود ہیں؟", "a": "RAVISN کا دفتر 41، میکلوڈ روڈ، لاہور میں ہے اور ہمارا امریکی دفتر کیسپر، وائیومنگ میں ہے۔", "lang": "urdu_nastaliq", "cat": "contact"},
    {"q": "آپ کی ویب سائٹ ہے؟", "a": "جی ہاں، ہماری ویب سائٹ ravisn.com ہے۔", "lang": "urdu_nastaliq", "cat": "contact"},
    {"q": "قیمت کیا ہے؟", "a": "قیمت آپ کے پروجیکٹ کے اسکوپ پر منحصر ہے۔ ہم مفت مشاورت کے بعد کوٹیشن فراہم کرتے ہیں۔", "lang": "urdu_nastaliq", "cat": "pricing"},
    {"q": "اس کی قیمت کتنی ہے؟", "a": "قیمت بزنس کی ضروریات اور پروجیکٹ اسکوپ پر منحصر ہے۔ فری کنسلٹیشن کے بعد کسٹم کوٹ دیا جاتا ہے۔", "lang": "urdu_nastaliq", "cat": "pricing"},
    {"q": "کیا ڈیمو مل سکتا ہے؟", "a": "جی ہاں، آپ ابھی RAVISN واٹس ایپ اسسٹنٹ سے چیٹ کر رہے ہیں۔ کسٹم ڈیمو فری مشاورت کے بعد دیا جا سکتا ہے۔", "lang": "urdu_nastaliq", "cat": "demo"},
    {"q": "شروع کیسے کروں؟", "a": "واٹس ایپ پر فری کنسلٹیشن بک کریں، اپنی بزنس ضرورت بتائیں اور ہماری ٹیم رہنمائی کرے گی۔", "lang": "urdu_nastaliq", "cat": "onboarding"},
    {"q": "ریئل اسٹیٹ کے لیے AI ہے؟", "a": "جی ہاں! ریئل اسٹیٹ کے لیے لیڈ کوالیفکیشن، واٹس ایپ فالو اپس اور وائس ایجنٹس آٹومیٹ کیے جا سکتے ہیں۔", "lang": "urdu_nastaliq", "cat": "industries"},
    {"q": "ریسٹورنٹ کے لیے AI بن سکتا ہے؟", "a": "جی ہاں، کسٹمر سوالات، بکنگز اور لیڈز آٹومیٹ کی جا سکتی ہیں۔", "lang": "urdu_nastaliq", "cat": "industries"},
    {"q": "کیا سپورٹ ملتی ہے؟", "a": "جی ہاں، ڈیلیوری کے بعد جاری سپورٹ اور آپٹمائزیشن فراہم کی جاتی ہے۔", "lang": "urdu_nastaliq", "cat": "support"},
    {"q": "سیٹ اپ میں کتنا وقت لگتا ہے؟", "a": "زیادہ تر AI آٹومیشن پروجیکٹس 1 تا 4 ہفتوں میں مکمل ہو جاتے ہیں۔", "lang": "urdu_nastaliq", "cat": "timeline"}
]


class RAVISNKnowledgeEngine:
    """Ultra-fast, high-precision in-memory QA & Domain matcher."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strips punctuation, lowercases, and cleans extra whitespace."""
        clean = text.lower().strip()
        clean = re.sub(r"[^\w\s\u0600-\u06FF]", " ", clean)
        return " ".join(clean.split())

    @classmethod
    def find_best_qa_match(
        cls,
        query: str,
        threshold: float = 0.68,
        db_session = None,
        tenant_id: str = None,
        **kwargs
    ) -> Optional[Tuple[Dict[str, str], float]]:
        """Finds the best semantic/lexical match in the database KB and RAVISN curated dataset."""
        norm_q = cls.normalize_text(query)
        if not norm_q:
            return None

        q_words = set(norm_q.split())
        db_session = db_session or kwargs.get("db_session")
        tenant_id = tenant_id or kwargs.get("tenant_id")

        # 0. First Priority: Check Database Knowledge Base (Frontend entries like CEO, custom Q&A)
        if db_session:
            try:
                from ..models.knowledge import KnowledgeEntry
                db_entries = db_session.query(KnowledgeEntry).filter(
                    (KnowledgeEntry.tenant_id == tenant_id) | (KnowledgeEntry.tenant_id == "default"),
                    KnowledgeEntry.is_active == True
                ).all()

                for entry in db_entries:
                    e_q_norm = cls.normalize_text(entry.question)
                    if norm_q == e_q_norm or norm_q in e_q_norm or e_q_norm in norm_q:
                        return ({"q": entry.question, "a": entry.answer, "lang": "english", "cat": "custom_kb"}, 1.0)
                    
                    # Keyword check (e.g. "ceo" in entry.question and "ceo" in user query)
                    e_words = set(e_q_norm.split())
                    if any(k in q_words for k in ["ceo", "founder", "owner", "boss", "director"]) and any(k in e_words for k in ["ceo", "founder", "owner", "boss", "director"]):
                        return ({"q": entry.question, "a": entry.answer, "lang": "english", "cat": "custom_kb"}, 1.0)
                    
                    seq_ratio = difflib.SequenceMatcher(None, norm_q, e_q_norm).ratio()
                    if seq_ratio >= 0.65:
                        return ({"q": entry.question, "a": entry.answer, "lang": "english", "cat": "custom_kb"}, seq_ratio)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error querying DB KnowledgeEntry in find_best_qa_match: {e}")

        # Direct keyword specific checks for critical contact facts
        if any(w in q_words for w in ["email", "mail", "gmail", "e-mail"]):
            for item in RAVISN_QA_DATA:
                if item["cat"] == "contact" and "email" in item["q"].lower():
                    if re.search(r"[\u0600-\u06FF]", query) and item["lang"] == "urdu_nastaliq":
                        return (item, 1.0)
                    elif any(k in norm_q for k in ["kya", "hai", "ka"]) and item["lang"] == "roman_urdu":
                        return (item, 1.0)
                    elif item["lang"] == "english":
                        return (item, 1.0)

        if any(w in q_words for w in ["phone", "number", "whatsapp", "call", "rabta"]):
            if not any(w in q_words for w in ["book", "demo", "automation", "automate"]):
                for item in RAVISN_QA_DATA:
                    if item["cat"] == "contact" and "number" in item["q"].lower():
                        if re.search(r"[\u0600-\u06FF]", query) and item["lang"] == "urdu_nastaliq":
                            return (item, 1.0)
                        elif any(k in norm_q for k in ["kya", "hai", "ka"]) and item["lang"] == "roman_urdu":
                            return (item, 1.0)
                        elif item["lang"] == "english":
                            return (item, 1.0)

        if any(w in q_words for w in ["located", "location", "address", "office", "kahan"]):
            for item in RAVISN_QA_DATA:
                if item["cat"] == "contact" and ("located" in item["q"].lower() or "kahan" in item["q"].lower() or "موجود" in item["q"]):
                    if re.search(r"[\u0600-\u06FF]", query) and item["lang"] == "urdu_nastaliq":
                        return (item, 1.0)
                    elif any(k in norm_q for k in ["kahan", "hai"]) and item["lang"] == "roman_urdu":
                        return (item, 1.0)
                    elif item["lang"] == "english":
                        return (item, 1.0)

        if any(w in q_words for w in ["website", "site", "web"]):
            for item in RAVISN_QA_DATA:
                if item["cat"] == "contact" and "website" in item["q"].lower():
                    return (item, 1.0)

        if any(w in q_words for w in ["instagram", "insta", "handle"]):
            for item in RAVISN_QA_DATA:
                if item["cat"] == "contact" and "instagram" in item["q"].lower():
                    return (item, 1.0)

        best_item = None
        best_score = 0.0


        for item in RAVISN_QA_DATA:
            target_norm = cls.normalize_text(item["q"])
            if norm_q == target_norm:
                return (item, 1.0)

            # Sequence matcher ratio
            seq_ratio = difflib.SequenceMatcher(None, norm_q, target_norm).ratio()

            # Word Jaccard overlap
            target_words = set(target_norm.split())
            if target_words:
                overlap = len(q_words.intersection(target_words)) / len(target_words.union(q_words))
            else:
                overlap = 0.0

            combined_score = (seq_ratio * 0.6) + (overlap * 0.4)

            if combined_score > best_score:
                best_score = combined_score
                best_item = item

        if best_item and best_score >= threshold:
            return (best_item, best_score)

        return None


class BookingDialogManager:
    """Manages stateful multi-turn demo & consultation booking flow."""

    @staticmethod
    def is_user_asking_question(text: str) -> bool:
        """Checks if the user input is a side question rather than answering the prompt."""
        question_starters = [
            "who", "where", "what", "why", "how", "when", "can i", "can you", "is there", "do you", "tell me",
            "kahan", "kaun", "kya", "kab", "kidhar", "kon", "konsa", "kese", "kaise", "kitne", "kitna", "batao"
        ]
        lower_text = text.lower().strip()
        words = lower_text.split()
        if not words:
            return False
        
        if "?" in lower_text:
            return True
            
        first_word = words[0]
        if first_word in question_starters or any(lower_text.startswith(qs + " ") for qs in question_starters):
            return True
            
        return False


    @staticmethod
    def detect_booking_intent(text: str) -> bool:
        clean = text.lower()
        booking_keywords = [
            "book", "booking", "demo", "consultation", "meeting", "schedule",
            "reserve", "appointment", "demo chahiye", "demo chahye", "free demo",
            "free consultation", "want a demo", "want demo", "book demo", "book call",
            "call book", "demo book"
        ]
        return any(re.search(rf"\b{re.escape(k)}\b", clean) for k in booking_keywords)

    @classmethod
    def process_turn(
        cls,
        user_message: str,
        current_step: str,
        booking_data: Dict[str, Any],
        language: str = "english",
        db_session = None,
        tenant_id: str = None,
        whatsapp_account_id: str = None,
        phone_number: str = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> Tuple[str, str, Dict[str, Any], bool]:
        """
        Executes strict 3-step conversational slot-filling with interruption guardrail:
        Returns (assistant_reply, next_step, updated_booking_data, is_completed)
        """
        data = dict(booking_data or {})
        msg = user_message.strip()
        msg_lower = msg.lower()
        step = (current_step or "idle").lower()

        # 0. Check for Explicit New Booking Intent Trigger
        if cls.detect_booking_intent(msg):
            step = "idle"
            data = {}

        # 1. Check for Memory Recall / Review
        is_memory_recall = any(k in msg_lower for k in ["detail", "details", "kya share kiya", "what details", "give me the detail", "kya details", "meri detail", "what i share", "which detail"])
        if is_memory_recall and data and step != "idle":
            ind = data.get("industry", "N/A")
            nm = data.get("name", "N/A")
            em = data.get("email", "N/A")
            srv = data.get("service_needed", "N/A")
            if nm != "N/A" or ind != "N/A":
                if language == "roman_urdu":
                    reply = f"Aap ne yeh details share ki hain:\n- **Naam**: {nm}\n- **Email**: {em}\n- **Industry**: {ind}\n- **Service**: {srv}\n\nAap ki information bilkul safe hai aur hamari engineering team is par kaam kar rahi hai."
                elif language == "urdu_nastaliq":
                    reply = f"آپ نے یہ تفصیلات فراہم کی ہیں:\n- **نام**: {nm}\n- **ای میل**: {em}\n- **شعبہ**: {ind}\n- **سروس**: {srv}\n\nہماری ٹیم اس کا جائزہ لے رہی ہے۔"
                else:
                    reply = f"You shared:\n- **Name**: {nm}\n- **Email**: {em}\n- **Industry**: {ind}\n- **Service**: {srv}\n\nYour details are securely stored and our engineering team is currently reviewing your request."
                return reply, "completed", data, True


        # Guardrail: Check if user interrupted with a question mid-booking sequence
        if step in ("awaiting_industry", "awaiting_contact", "awaiting_service") and cls.is_user_asking_question(msg):
            qa_res = RAVISNKnowledgeEngine.find_best_qa_match(msg, threshold=0.55, db_session=db_session, tenant_id=tenant_id)
            if qa_res:
                ans = qa_res[0]["a"]
            else:
                if any(w in msg_lower for w in ["office", "location", "address", "kahan"]):
                    ans = "Our office is located at 41, McLeod Road, Lahore, and our US office is at 312 W 2ND ST 1992 CASPER, WY 82601."
                elif any(w in msg_lower for w in ["ceo", "owner", "founder"]):
                    ans = "The CEO and founder of RAVISN is Usama Anis."
                else:
                    ans = "RAVISN provides 24/7 AI automation solutions including WhatsApp chatbots, AI voice agents, and CRM integrations."

            if step == "awaiting_industry":
                if language == "roman_urdu":
                    prompt_remind = "\n\nAb baraye meherbani batayein aap ka kis industry ya business domain mein kaam hai? (e.g. HVAC, Real Estate, E-commerce)"
                elif language == "urdu_nastaliq":
                    prompt_remind = "\n\nاب برائے مہربانی بتائیں آپ کا کس شعبے یا کاروبار میں کام ہے؟"
                else:
                    prompt_remind = "\n\nNow, which industry or business domain are you operating in? (e.g., HVAC, Real Estate, E-commerce, etc.)"
            elif step == "awaiting_contact":
                if language == "roman_urdu":
                    prompt_remind = "\n\nAb baraye meherbani apna **Naam** aur **Email address** share karein?"
                elif language == "urdu_nastaliq":
                    prompt_remind = "\n\nاب برائے مہربانی اپنا نام اور ای میل ایڈریس بتائیں؟"
                else:
                    prompt_remind = "\n\nNow, could you please share your **Name** and **Email address** so we can set up your profile?"
            elif step == "awaiting_service":
                if language == "roman_urdu":
                    prompt_remind = "\n\nAb batayein aap kaun si specific AI service ya automation implement karna chahte hain?"
                elif language == "urdu_nastaliq":
                    prompt_remind = "\n\nاب بتائیں آپ کون سی مخصوص سروس یا آٹومیشن شروع کرنا چاہتے ہیں؟"
                else:
                    prompt_remind = "\n\nNow, what specific service or automation are you looking to implement?"
            else:
                prompt_remind = ""

            reply = f"{ans}{prompt_remind}"
            return reply, step, data, False


        if step not in ("awaiting_industry", "awaiting_contact", "awaiting_service"):
            step = "idle"

        # 1. Step: IDLE -> Trigger Demo
        if step == "idle":
            next_step = "awaiting_industry"
            data = {}  # start fresh booking data
            if language == "urdu_nastaliq":
                reply = "ہم آپ کے لیے مفت ڈیمو شیڈول کرنے کے لیے تیار ہیں! 🚀\n\nآپ کا کس شعبے یا کاروبار میں کام ہے؟ (مثلاً: HVAC، رئیل اسٹیٹ، ای کامرس، کلینک وغیرہ)"
            elif language == "roman_urdu":
                reply = "Zaroor! Hum aap ke liye free demo arrange kar dete hain! 🚀\n\nAap ka kis industry ya business domain mein kaam hai? (e.g., HVAC, Real Estate, E-commerce, Healthcare waghera)"
            else:
                reply = (
                    "We would be glad to arrange a free demo for you! 🚀\n\n"
                    "Which industry or business domain are you operating in? (e.g., HVAC, Real Estate, E-commerce, Healthcare, etc.)"
                )
            return reply, next_step, data, False



        # 2. Step: Awaiting Industry
        if step == "awaiting_industry":
            industry = msg.strip().title()
            data["industry"] = industry
            next_step = "awaiting_contact"

            if language == "urdu_nastaliq":
                reply = (
                    f"جی بالکل! ہم {industry} کے شعبے کے لیے خصوصی AI سلوشنز تیار کرتے ہیں۔ 💡\n\n"
                    "پروفائل سیٹ اپ کے لیے برائے مہربانی اپنا **نام** اور **ای میل ایڈریس** بتائیں؟"
                )
            elif language == "roman_urdu":
                reply = (
                    f"Ji bilkul! Hum {industry} industry ke liye specialized AI solutions aur agents develop karte hain. 💡\n\n"
                    "Profile setup karne ke liye baraye meherbani apna **Naam** aur **Email address** share karein?"
                )
            else:
                reply = (
                    f"Yes, absolutely! We develop specialized AI solutions and agents for the {industry} industry. 💡\n\n"
                    "Could you please share your **Name** and **Email address** so we can set up your profile?"
                )
            return reply, next_step, data, False

        # 3. Step: Awaiting Contact (Name & Email)
        if step == "awaiting_contact":
            email = None
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', msg)
            if email_match:
                email = email_match.group(0)

            # Name extraction
            name_text = msg
            if email:
                name_text = msg.replace(email, "")
            name_text = re.sub(r"[,\-\|\n]", " ", name_text).strip()
            name_parts = [w for w in name_text.split() if w.lower() not in ("my", "name", "is", "mera", "naam", "email", "mail", "and", "aur")]
            name = " ".join(name_parts).strip().title() if name_parts else (name_text.title() or "Friend")

            data["name"] = name
            data["email"] = email or "provided_on_chat"
            next_step = "awaiting_service"

            if language == "urdu_nastaliq":
                reply = (
                    f"آپ سے رابطہ کر کے خوشی ہوئی، {name}!\n\n"
                    "آپ کون سی مخصوص سروس یا آٹومیشن چاہتے ہیں؟ (مثلاً: واٹس ایپ AI سیلز ایجنٹ، لیڈ کوالیفکیشن، کسٹمر سپورٹ وغیرہ)"
                )
            elif language == "roman_urdu":
                reply = (
                    f"Nice to meet you, {name}!\n\n"
                    "Aap kaun si specific service ya automation implement karna chahte hain? (e.g., 24/7 WhatsApp AI Sales Agent, Lead Qualification, Customer Support waghera)"
                )
            else:
                reply = (
                    f"Nice to meet you, {name}!\n\n"
                    "What specific service or automation are you looking to implement? "
                    "(e.g., 24/7 WhatsApp AI Sales Agent, Lead Qualification, Customer Support, etc.)"
                )
            return reply, next_step, data, False

        # 4. Step: Awaiting Service & Persistence
        # 4. Step: Awaiting Service & Persistence
        if step == "awaiting_service":
            service_needed = msg.strip()
            data["service_needed"] = service_needed
            next_step = "completed"

            # Persist to DemoBooking and Booking tables in database
            if db_session:
                try:
                    import json
                    from ..models.booking import DemoBooking, Booking
                    
                    booking_rec = DemoBooking(
                        tenant_id=tenant_id or "default",
                        whatsapp_account_id=whatsapp_account_id or "default",
                        phone_number=phone_number or "whatsapp_inbound",
                        name=data.get("name"),
                        email=data.get("email"),
                        industry=data.get("industry"),
                        service_needed=data.get("service_needed"),
                        raw_conversation=json.dumps(conversation_history or [], ensure_ascii=False),
                        status="pending"
                    )
                    db_session.add(booking_rec)

                    # Also persist into standard Booking table for dashboard visibility
                    standard_booking = Booking(
                        tenant_id=tenant_id or "default",
                        channel=whatsapp_account_id or "whatsapp",
                        customer_name=data.get("name"),
                        name=data.get("name"),
                        customer_email=data.get("email"),
                        customer_phone=phone_number or "whatsapp_inbound",
                        contact=phone_number or "whatsapp_inbound",
                        service_name=data.get("service_needed") or "AI Automation Demo",
                        notes=f"Industry: {data.get('industry', 'N/A')} | Service: {data.get('service_needed', 'N/A')}",
                        preferred_time="Demo Booking Request",
                        status="pending"
                    )
                    db_session.add(standard_booking)
                    db_session.commit()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error persisting demo booking: {e}")

            if language == "urdu_nastaliq":
                reply = (
                    "آپ کے قیمتی وقت کا بہت شکریہ! 🙏\n\n"
                    "ہم نے آپ کی تمام تفصیلات محفوظ کر لی ہیں۔ ہماری ٹیکنیکل ٹیم جلد آپ سے رابطہ کرے گی۔"
                )
            elif language == "roman_urdu":
                reply = (
                    "Thank you for your precious time! 🙏\n\n"
                    "Hum ne aap ki saari details record kar li hain. Hamari technical team aap ki requirements review karke jald WhatsApp par rabta karegi."
                )
            else:
                reply = (
                    "Thank you for your precious time! 🙏\n\n"
                    "We have recorded all your details. Our technical team will review your requirements and contact you shortly."
                )
            return reply, next_step, data, True

        # Check for memory recall inquiry post-booking
        if step == "completed" or any(k in msg_lower for k in ["detail", "details", "kya detail", "meri detail", "what i share"]):
            ind = data.get("industry", "N/A")
            nm = data.get("name", "N/A")
            em = data.get("email", "N/A")
            srv = data.get("service_needed", "N/A")
            if nm != "N/A" or ind != "N/A":
                if language == "roman_urdu":
                    reply = f"Aap ne yeh details share ki hain:\n- **Naam**: {nm}\n- **Email**: {em}\n- **Industry**: {ind}\n- **Service**: {srv}\n\nAap ki information bilkul safe hai aur hamari engineering team is par kaam kar rahi hai."
                elif language == "urdu_nastaliq":
                    reply = f"آپ نے یہ تفصیلات فراہم کی ہیں:\n- **نام**: {nm}\n- **ای میل**: {em}\n- **شعبہ**: {ind}\n- **سروس**: {srv}\n\nہماری ٹیم اس کا جائزہ لے رہی ہے۔"
                else:
                    reply = f"You shared:\n- **Name**: {nm}\n- **Email**: {em}\n- **Industry**: {ind}\n- **Service**: {srv}\n\nYour details are securely stored and our engineering team is currently reviewing your request."
                return reply, "completed", data, True

        # Completed or default
        return "Thank you! Our team has all your details and will connect with you shortly.", "completed", data, True


