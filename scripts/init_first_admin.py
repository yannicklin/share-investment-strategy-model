"""
Initialize First Admin for Bot Trading System

Creates the first admin user in the whitelist to bootstrap the authentication system.

Usage:
    python scripts/init_first_admin.py +61431121011 telegram
    python scripts/init_first_admin.py 0431121011 sms

Args:
    phone: Phone number (accepts +61431121011 or 0431121011 format)
    notification: Notification method (telegram/sms/both) - default: telegram

Author: Yannick
Copyright (c) 2026 Yannick
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot import create_app, db
from app.bot.shared.models import AdminWhitelist
from app.bot.services.phone_utils import validate_and_normalize, format_phone_display
from app.bot.services.auth_utils import hash_phone_number


def init_first_admin(phone: str, notification_preference: str = 'telegram'):
    """
    Initialize first admin in whitelist.
    
    Args:
        phone: Phone number (any format: 0431121011, +61431121011, etc.)
        notification_preference: telegram, sms, or both
    
    Returns:
        True if successful, False otherwise
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Normalize phone number
            print(f"📱 Normalizing phone number: {phone}")
            normalized_phone = validate_and_normalize(phone)
            display_phone = format_phone_display(normalized_phone)
            print(f"   ✅ Normalized: {normalized_phone}")
            print(f"   ✅ Display: {display_phone}")
            
            # Hash phone number
            print(f"\n🔐 Hashing phone number...")
            phone_hash = hash_phone_number(normalized_phone)
            print(f"   ✅ Hash generated: {phone_hash[:32]}...")
            
            # Check if already exists
            existing = AdminWhitelist.query.filter_by(phone_number_hash=phone_hash).first()
            if existing:
                print(f"\n⚠️  Admin already exists:")
                print(f"   ID: {existing.id}")
                print(f"   Phone: {existing.display_phone}")
                print(f"   Notification: {existing.notification_preference}")
                print(f"   Active: {existing.is_active}")
                print(f"   Created: {existing.created_at}")
                
                # Ask if user wants to update
                response = input("\n   Update this admin? (y/n): ").lower()
                if response == 'y':
                    existing.notification_preference = notification_preference
                    existing.is_active = True
                    existing.display_phone = display_phone
                    db.session.commit()
                    print(f"\n✅ Admin updated successfully!")
                    return True
                else:
                    print(f"\n❌ Skipped.")
                    return False
            
            # Create new admin
            print(f"\n➕ Creating admin...")
            admin = AdminWhitelist(
                phone_number_hash=phone_hash,
                display_phone=display_phone,
                notification_preference=notification_preference,
                is_active=True,
                created_by='system'
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"\n✅ First admin created successfully!")
            print(f"   ID: {admin.id}")
            print(f"   Phone: {display_phone}")
            print(f"   Notification: {notification_preference}")
            print(f"\n🎉 You can now login to the admin panel with this phone number!")
            
            return True
        
        except ValueError as e:
            print(f"\n❌ Invalid phone number: {str(e)}")
            return False
        except Exception as e:
            print(f"\n❌ Error creating admin: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/init_first_admin.py <phone> [notification_preference]")
        print("\nExamples:")
        print("  python scripts/init_first_admin.py +61431121011")
        print("  python scripts/init_first_admin.py 0431121011 telegram")
        print("  python scripts/init_first_admin.py 0431-121-011 sms")
        print("\nNotification preferences: telegram, sms, line, telegram+line, all")
        sys.exit(1)
    
    phone = sys.argv[1]
    notification_preference = sys.argv[2] if len(sys.argv) > 2 else 'telegram'
    
    # Validate notification preference
    valid_prefs = ['telegram', 'sms', 'line', 'telegram+line', 'sms+line', 'telegram+sms', 'all']
    if notification_preference not in valid_prefs:
        print(f"❌ Invalid notification preference: {notification_preference}")
        print(f"   Must be one of: {', '.join(valid_prefs)}")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 First Admin Initialization")
    print("=" * 60)
    
    success = init_first_admin(phone, notification_preference)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
