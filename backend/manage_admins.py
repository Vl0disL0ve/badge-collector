import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import User

def list_admins():
    db = SessionLocal()
    try:
        admins = db.query(User).filter(User.is_admin == True).all()
        print()
        if not admins:
            print("📭 Нет администраторов в базе данных")
        else:
            print(f"👑 Администраторы ({len(admins)}):")
            for admin in admins:
                print(f"   - {admin.email} (ID: {admin.id})")
        return admins
    except Exception as e:
        print(f"❌ Ошибка при чтении БД: {e}")
        return []
    finally:
        db.close()

def add_admin(email):
    print(f"\n🔍 Ищем пользователя с email: {email}")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ Пользователь с email '{email}' не найден")
            print("\n📋 Список всех пользователей в БД:")
            all_users = db.query(User).all()
            if all_users:
                for u in all_users:
                    print(f"   - {u.email} (ID: {u.id})")
            else:
                print("   (нет пользователей)")
            return False
        
        if user.is_admin:
            print(f"⚠️ Пользователь '{email}' уже является администратором")
            return True
        
        user.is_admin = True
        db.commit()
        print(f"✅ Пользователь '{email}' назначен администратором")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def remove_admin(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ Пользователь с email '{email}' не найден")
            return False
        
        if not user.is_admin:
            print(f"⚠️ Пользователь '{email}' не является администратором")
            return True
        
        user.is_admin = False
        db.commit()
        print(f"✅ Права администратора сняты с пользователя '{email}'")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def make_first_user_admin():
    """Сделать первого пользователя администратором (для отладки)"""
    db = SessionLocal()
    try:
        first_user = db.query(User).order_by(User.id).first()
        if first_user:
            if not first_user.is_admin:
                first_user.is_admin = True
                db.commit()
                print(f"✅ Пользователь '{first_user.email}' назначен администратором")
            else:
                print(f"ℹ️ Пользователь '{first_user.email}' уже администратор")
        else:
            print("❌ В базе нет пользователей")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python manage_admins.py --list")
        print("  python manage_admins.py user@example.com --add")
        print("  python manage_admins.py user@example.com --remove")
        print("  python manage_admins.py --make-first-admin  # сделать первого пользователя админом")
        sys.exit(1)
    
    if "--make-first-admin" in sys.argv:
        make_first_user_admin()
        sys.exit(0)
    
    email = None
    action = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--list":
            action = "list"
        elif arg == "--add":
            action = "add"
        elif arg == "--remove":
            action = "remove"
        elif not arg.startswith("--") and email is None:
            email = arg
    
    if action == "list":
        list_admins()
    elif action == "add" and email:
        add_admin(email)
    elif action == "remove" and email:
        remove_admin(email)
    else:
        print("❌ Неверные параметры")