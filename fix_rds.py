from sqlalchemy import create_engine, text
from app.config import settings
import sys

print("🔧 Fixing RDS payment_tokens table...")

engine = create_engine(settings.DATABASE_URL)

try:
    with engine.begin() as conn:  # Auto-commit transaction
        # Check if columns exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'payment_tokens' 
            AND column_name IN ('uses_total', 'uses_remaining', 'last_used_at');
        """))
        existing_columns = [row[0] for row in result]
        
        print(f"📊 Existing columns: {existing_columns}")
        
        # Add missing columns
        if 'uses_total' not in existing_columns:
            print("➕ Adding uses_total column...")
            conn.execute(text("""
                ALTER TABLE payment_tokens 
                ADD COLUMN uses_total INTEGER NOT NULL DEFAULT 2;
            """))
        
        if 'uses_remaining' not in existing_columns:
            print("➕ Adding uses_remaining column...")
            conn.execute(text("""
                ALTER TABLE payment_tokens 
                ADD COLUMN uses_remaining INTEGER NOT NULL DEFAULT 2;
            """))
        
        if 'last_used_at' not in existing_columns:
            print("➕ Adding last_used_at column...")
            conn.execute(text("""
                ALTER TABLE payment_tokens 
                ADD COLUMN last_used_at TIMESTAMP;
            """))
        
        # Migrate existing data
        print("🔄 Migrating existing token data...")
        conn.execute(text("""
            UPDATE payment_tokens 
            SET uses_total = 2,
                uses_remaining = CASE 
                    WHEN status = 'USED' THEN 0
                    WHEN status = 'UNUSED' THEN 2
                    WHEN status = 'REFUNDED' THEN 0
                    ELSE 1
                END,
                last_used_at = CASE 
                    WHEN used_at IS NOT NULL THEN used_at
                    ELSE NULL
                END
            WHERE uses_total IS NULL OR uses_remaining IS NULL;
        """))
        
        # Remove defaults
        print("🧹 Removing default values...")
        conn.execute(text("""
            ALTER TABLE payment_tokens 
            ALTER COLUMN uses_total DROP DEFAULT,
            ALTER COLUMN uses_remaining DROP DEFAULT;
        """))
        
        print("✅ Database fix complete!")
        
        # Verify
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'payment_tokens'
            AND column_name IN ('uses_total', 'uses_remaining', 'last_used_at')
            ORDER BY column_name;
        """))
        
        print("\n📋 Final column status:")
        for row in result:
            print(f"  ✓ {row[0]}: {row[1]} (default: {row[2]})")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)