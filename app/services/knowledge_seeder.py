import logging
from sqlalchemy.orm import Session
from ..models import Tenant, TenantKnowledgeChunk, KnowledgeEntry
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)

RAVISN_TOPICS = [
    {
        "category": "About",
        "title": "About RAVISN",
        "content": 'RAVISN is an AI Automation Agency — "AI Automation That Grows Your Business, On Autopilot." We combine creativity, strategy, and AI automation to build intelligent systems that streamline operations, generate qualified leads, and turn visitors into loyal customers. 300+ projects completed, 500+ customer reviews, 98% happy clients, 24/7 support. Website: ravisn.com'
    },
    {
        "category": "Services",
        "title": "Core AI Automation Services",
        "content": "AI Chatbot Development (24/7 chatbots that answer queries, qualify leads, improve engagement) | AI Voice Agents (automate inbound/outbound calls, bookings, follow-ups) | WhatsApp AI Automation (customer conversations, lead nurturing, appointment scheduling, support on WhatsApp Business) | Lead Qualification Automation (auto qualify, score, and route leads) | CRM Automation (connect CRM with AI workflows for lead management and follow-ups) | Appointment Booking Automation (AI schedules meetings, confirmations, reminders) | Email Marketing Automation (automated sequences that nurture leads) | Workflow Automation (eliminate repetitive tasks across apps and teams) | AI Knowledge Base (AI assistants trained on your business documents) | Customer Support Automation (24/7 AI chat and voice support) | Custom AI Solutions (fully tailored AI systems for your business processes)"
    },
    {
        "category": "Process",
        "title": "How We Work - 4 Step Process",
        "content": "Step 1: Discovery & Business Analysis — we understand your business and find automation gaps. Step 2: AI Strategy & Automation Planning — we design the right AI solution for you. Step 3: Development & System Integration — we build and connect it with your existing systems. Step 4: Deployment & Continuous Optimization — we launch, monitor, and keep improving it."
    },
    {
        "category": "Industries",
        "title": "Industries We Serve (Real Estate, Healthcare, etc.)",
        "content": "Real estate, HVAC & home services, restaurants, aesthetics & clinics, healthcare, legal services, e-commerce, and many more. Our solutions are industry-agnostic and fully customizable — any business with customer conversations, leads, or repetitive tasks can be automated."
    },
    {
        "category": "Timeline",
        "title": "Delivery Timeline",
        "content": "Most AI automation solutions are delivered within 1-4 weeks, depending on the scope of the project."
    },
    {
        "category": "Packages",
        "title": "Automation Packages & Plans",
        "content": "Basic Package: AI Chatbot Setup (Website), Lead Capture Automation, WhatsApp Integration, Appointment Booking, Basic CRM Integration, Free Consultation, 30 Days Support, Basic Training. | All-in-One Solution (Recommended): Everything in Basic + AI Voice Agent, CRM Automation, Email & SMS Automation, Lead Qualification AI, Workflow Automation, Monthly Performance Report, Free Strategy Session, 60 Days Support, AI Workflow Optimization. | Premium Package: Everything in All-in-One + Custom AI Agent Development, Multi-Channel Automation (WhatsApp + Voice + Email AI), Advanced CRM & API Integrations, Dedicated Account Manager, Priority Support, AI Growth Consultation, 90 Days Premium Support, Free Future Optimization."
    },
    {
        "category": "Pricing Policy",
        "title": "Pricing & Quotation Policy",
        "content": "Never mention any specific price or amount. Every business is unique, so pricing depends on business needs and project scope. Our team shares a custom quote after a free consultation."
    },
    {
        "category": "Why Choose Us",
        "title": "Why Choose RAVISN",
        "content": "We're not just another agency — we're your strategic partner in growth. Proven expertise: AI Automation, AI Chatbots & Agents, Workflow Automation, Lead Generation Automation. We deliver custom-built systems, not generic templates, with ongoing support and optimization."
    },
    {
        "category": "Contact",
        "title": "Contact Details & Locations",
        "content": "WhatsApp: +1 (564) 222-6889 | Email: Ravisn.uk@gmail.com | Instagram: @ravisnofficial | Website: ravisn.com | US Office: 312 W 2ND ST 1992 CASPER, WY 82601 | Pakistan Office: 41, McLeod Road, Lahore."
    },
    {
        "category": "Free Offer",
        "title": "Free AI Consultation Offer",
        "content": "Free consultation for every new client — book a call on WhatsApp, share your business requirements, and our experts will analyze your workflows and recommend the best AI automation solution."
    }
]

RAVISN_FAQS = [
    {
        "question": "What services do you offer?",
        "answer": "We provide end-to-end AI automation solutions: AI Chatbots, AI Voice Agents, WhatsApp Automation, CRM Automation, Workflow Automation, Lead Qualification, Appointment Booking, Email Automation, AI Knowledge Base, Customer Support Automation, and fully Custom AI Solutions."
    },
    {
        "question": "What are the requirements to get started?",
        "answer": "Getting started is easy! Book a free consultation on WhatsApp, share your business requirements, and our experts will analyze your workflows, recommend the best solution, handle the implementation, and provide ongoing support."
    },
    {
        "question": "How do you decide the right strategy for my business?",
        "answer": "We analyze your business goals, existing processes, and customer journey to find where AI creates the biggest impact — then design a customized automation strategy for measurable results."
    },
    {
        "question": "What makes RAVISN different from other agencies?",
        "answer": "We build custom AI-powered systems (not generic templates) that increase efficiency, reduce costs, and fuel long-term growth — with real ongoing support and optimization after delivery."
    },
    {
        "question": "How long will it take to see results?",
        "answer": "Most AI automation solutions are delivered within 1-4 weeks depending on scope, so you quickly start automating tasks, engaging customers, and capturing more leads."
    },
    {
        "question": "Do you have experience in my industry?",
        "answer": "Yes! Our solutions are industry-agnostic and fully customizable. We work with real estate, HVAC, restaurants, aesthetics/clinics, healthcare, legal, e-commerce, and many other industries."
    },
    {
        "question": "How much does it cost?",
        "answer": "Pricing depends on your business needs and project scope — every business is unique. Book a free consultation and our team will share a custom quote for you."
    },
    {
        "question": "Can I see a demo?",
        "answer": "You're already talking to one! 😊 This WhatsApp assistant is built by RAVISN. For a demo tailored to your own business, our team can arrange one after a quick consultation."
    },
    {
        "question": "Where are you located?",
        "answer": "Our office is at 41, McLeod Road, Lahore, and our US office is in Casper, WY. We work with clients locally and globally — everything is handled online through WhatsApp and calls."
    },
    {
        "question": "How does payment work?",
        "answer": "Payment details and milestones are shared with your custom quote after the free consultation. Our team will guide you through the simple process."
    },
    {
        "question": "What is an AI agent?",
        "answer": "An AI agent is a smart assistant that talks to your customers automatically — answering questions, qualifying leads, booking appointments, and following up 24/7 on channels like WhatsApp, so you never miss a lead."
    },
    {
        "question": "Will an AI agent replace my staff?",
        "answer": "No — it supports them. The AI handles repetitive conversations and instant replies 24/7, while your team focuses on high-value work like closing deals and serving customers."
    },
    {
        "question": "Which platforms do you integrate with?",
        "answer": "We integrate with WhatsApp Business, websites, CRMs, Google Sheets, email/SMS tools, calendars, and custom systems via APIs — connected into one smart automated workflow."
    },
    {
        "question": "Do you provide support after delivery?",
        "answer": "Yes — every package includes support (30 to 90 days depending on package) plus training, and we offer continuous optimization to keep improving your system."
    },
    {
        "question": "Is my business data safe?",
        "answer": "Yes — your data stays in your own accounts and systems (like your Google Sheets and WhatsApp Business). We build the automation around your infrastructure."
    }
]


def seed_ravisn_knowledge(db: Session, tenant_id: str):
    """Ingests all RAVISN topics and FAQs into PostgreSQL/SQLite for high-precision retrieval."""
    # 1. Ingest Chunks
    for item in RAVISN_TOPICS:
        exists = db.query(TenantKnowledgeChunk).filter(
            TenantKnowledgeChunk.tenant_id == tenant_id,
            TenantKnowledgeChunk.chunk_title == item["title"]
        ).first()
        if not exists:
            chunk = TenantKnowledgeChunk(
                tenant_id=tenant_id,
                category=item["category"],
                chunk_title=item["title"],
                chunk_content=item["content"]
            )
            db.add(chunk)
        else:
            exists.category = item["category"]
            exists.chunk_content = item["content"]

    # 2. Ingest Legacy FAQs
    for faq in RAVISN_FAQS:
        exists = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.question == faq["question"]
        ).first()
        if not exists:
            entry = KnowledgeEntry(
                tenant_id=tenant_id,
                question=faq["question"],
                answer=faq["answer"],
                is_active=True
            )
            db.add(entry)
        else:
            exists.answer = faq["answer"]
            exists.is_active = True


    db.commit()
    logger.info(f"Seeded RAVISN knowledge base successfully for tenant {tenant_id}")


def seed_all_tenants():
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).all()
        if not tenants:
            t = Tenant(business_name="RAVISN", slug="ravisn-uk")
            db.add(t)
            db.commit()
            db.refresh(t)
            tenants = [t]
            
        for t in tenants:
            t.business_name = "RAVISN"
            seed_ravisn_knowledge(db, t.id)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_tenants()
    print("RAVISN Knowledge Base Seeded Successfully!")
