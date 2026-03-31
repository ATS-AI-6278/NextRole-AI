import datetime as dt
from app.core.db import SessionLocal, engine
from app.memory.relational.models import User, JobApplication
from app.memory.relational.repository import init_db, get_or_create_user_by_chat_id, create_job_application

def seed():
    # Ensure tables exist
    init_db(engine)
    
    db = SessionLocal()
    try:
        # Create user for the specific chat_id
        chat_id = "7979719022"
        user = get_or_create_user_by_chat_id(db, chat_id)
        
        # Add some mock applications
        mock_apps = [
            {"company": "Google", "role": "Software Engineer", "applied_at": dt.datetime.now() - dt.timedelta(days=2)},
            {"company": "OpenAI", "role": "AI Researcher", "applied_at": dt.datetime.now() - dt.timedelta(days=5)},
            {"company": "Anthropic", "role": "Frontend Developer", "applied_at": dt.datetime.now() - dt.timedelta(days=1)},
        ]
        
        for app in mock_apps:
            create_job_application(
                db,
                user_id=user.id,
                company=app["company"],
                role=app["role"],
                applied_at=app["applied_at"],
                source_message_id="msg_abc123"
            )
        
        print(f"Successfully seeded {len(mock_apps)} applications for chat_id: {chat_id}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
