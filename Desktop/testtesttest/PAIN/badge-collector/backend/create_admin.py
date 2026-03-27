import sys
import os
import argparse

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import User

def set_admin(email: str, remove: bool = False):
    """
    Установить или снять права администратора
    """
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ Пользователь с email '{email}' не найден")
            return False
        
        if remove:
            if not user.is_admin:
                print(f"⚠️ Пользователь '{email}' уже не является администратором")
                return True
            
            user.is_admin = False
            db.commit()
            print(f"✅ Права администратора сняты с пользователя '{email}'")
            return True
        else:
            if user.is_admin:
                print(f"⚠️ Пользователь '{email}' уже является администратором")
                return True
            
            user.is_admin = True
            db.commit()
            print(f"✅ Пользователь '{email}' назначен администратором")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()

def list_admins():
    """
    Показать всех администраторов
    """
    db = SessionLocal()
    try:
        admins = db.query(User).filter(User.is_admin == True).all()
        
        if not admins:
            print("📭 Нет пользователей с правами администратора")
            return
        
        print("\n👑 Администраторы:")
        print("-" * 40)
        for admin in admins:
            print(f"  • {admin.email} (ID: {admin.id})")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description='Управление правами администратора')
    parser.add_argument('email', nargs='?', help='Email пользователя')
    parser.add_argument('-r', '--remove', action='store_true', help='Снять права администратора')
    parser.add_argument('-l', '--list', action='store_true', help='Показать всех администраторов')
    
    args = parser.parse_args()
    
    if args.list:
        list_admins()
    elif args.email:
        set_admin(args.email, args.remove)
    else:
        parser.print_help()
        print("\nПримеры использования:")
        print("  python create_admin.py user@example.com          # назначить админом")
        print("  python create_admin.py user@example.com -r       # снять права")
        print("  python create_admin.py -l                        # список админов")

if __name__ == "__main__":
    main()