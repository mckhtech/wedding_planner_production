#!/usr/bin/env python3
"""
Manual Migration Script
Run this if Alembic migration hasn't been applied yet

Usage:
    python manual_migration.py
"""

import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from app.config import settings  # Assuming you have database URL in settings

def run_migration():
    """
    Run migration manually using raw SQL
    """
    print("=" * 60)
    print("🚀 MANUAL MIGRATION SCRIPT")
    print("=" * 60)
    
    # Get database connection
    try:
        # Construct database URL from settings
        DATABASE_URL = settings.DATABASE_URL
        print(f"\n📡 Connecting to database...")
        
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
        print("✅ Connected successfully!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        sys.exit(1)
    
    try:
        # Start transaction
        trans = connection.begin()
        
        # ============================================
        # PART 1: Add Unlimited Credits Columns
        # ============================================
        print("\n" + "=" * 60)
        print("PART 1: Adding Unlimited Credits Tracking")
        print("=" * 60)
        
        # Check if columns already exist
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' 
            AND column_name IN ('unlimited_free_enabled_at', 'original_free_credits')
        """))
        existing_columns = [row[0] for row in result]
        
        if 'unlimited_free_enabled_at' in existing_columns:
            print("⏭️  Columns already exist, skipping Part 1...")
        else:
            print("📝 Adding 'unlimited_free_enabled_at' column...")
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN unlimited_free_enabled_at TIMESTAMP
            """))
            print("✅ Column added!")
            
            print("📝 Adding 'original_free_credits' column...")
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN original_free_credits INTEGER
            """))
            print("✅ Column added!")
            
            print("📝 Updating existing users...")
            connection.execute(text("""
                UPDATE users 
                SET original_free_credits = free_credits_remaining,
                    unlimited_free_enabled_at = :now
                WHERE original_free_credits IS NULL
            """), {"now": datetime.utcnow()})
            print("✅ Existing users updated!")
        
        # ============================================
        # PART 2: Create Contacts Table
        # ============================================
        print("\n" + "=" * 60)
        print("PART 2: Creating Contacts Table")
        print("=" * 60)
        
        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'contacts'
        """))
        
        if result.fetchone():
            print("⏭️  Contacts table already exists, skipping Part 2...")
        else:
            print("📝 Creating contacts table...")
            connection.execute(text("""
                CREATE TABLE contacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    email VARCHAR NOT NULL,
                    phone VARCHAR NOT NULL,
                    event_date VARCHAR,
                    message TEXT,
                    is_read BOOLEAN NOT NULL DEFAULT FALSE,
                    is_responded BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    admin_notes TEXT
                )
            """))
            print("✅ Table created!")
            
            print("📝 Creating indexes...")
            connection.execute(text("""
                CREATE INDEX ix_contacts_id ON contacts(id)
            """))
            connection.execute(text("""
                CREATE INDEX ix_contacts_email ON contacts(email)
            """))
            connection.execute(text("""
                CREATE INDEX ix_contacts_created_at ON contacts(created_at)
            """))
            print("✅ Indexes created!")
        
        # Commit transaction
        trans.commit()
        
        # ============================================
        # VERIFICATION
        # ============================================
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        
        # Check users table columns
        print("\n📊 Users table columns:")
        result = connection.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            AND column_name IN (
                'free_credits_remaining', 
                'unlimited_free_enabled_at', 
                'original_free_credits'
            )
            ORDER BY column_name
        """))
        for row in result:
            print(f"  ✓ {row[0]}: {row[1]}")
        
        # Check contacts table
        print("\n📊 Contacts table structure:")
        result = connection.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'contacts'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  ✓ {row[0]}: {row[1]}")
        
        # Count existing data
        result = connection.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        
        result = connection.execute(text("SELECT COUNT(*) FROM contacts"))
        contact_count = result.fetchone()[0]
        
        print(f"\n📈 Database stats:")
        print(f"  Users: {user_count}")
        print(f"  Contacts: {contact_count}")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nWhat's enabled now:")
        print("  1. ✨ Users can generate UNLIMITED free templates")
        print("  2. 📧 Contact form can receive inquiries")
        print("  3. 📊 Historical credit data preserved")
        print("\nNext steps:")
        print("  1. Restart your backend server")
        print("  2. Test free template generation (should work unlimited times)")
        print("  3. Test contact form submission")
        print("  4. Check admin panel for contact inquiries")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        trans.rollback()
        sys.exit(1)
        
    finally:
        connection.close()
        engine.dispose()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will modify your database!")
    print("Make sure you have a backup before proceeding.\n")
    
    response = input("Continue with migration? (yes/no): ").strip().lower()
    
    if response == 'yes':
        run_migration()
    else:
        print("\n❌ Migration cancelled.")
        sys.exit(0)