# verify_migration.py
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'payment_tokens'
        ORDER BY ordinal_position;
    """))
    
    print("Columns in payment_tokens table:")
    for row in result:
        print(f"  - {row[0]}: {row[1]}")