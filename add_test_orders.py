from sqlalchemy.orm import Session
from database import SessionLocal, User, Service, Order
import json
from datetime import datetime

def add_test_orders():
    db: Session = SessionLocal()
    try:
        # Проверяем, есть ли пользователь
        user = db.query(User).filter(User.telegram_id == 610269479).first()
        if not user:
            user = User(telegram_id=610269479, points=100)
            db.add(user)
            db.commit()
            db.refresh(user)
            print("Добавлен тестовый пользователь")

        # Проверяем, есть ли услуги
        services = db.query(Service).all()
        if not services:
            print("Нет услуг в базе. Запустите main.py для инициализации.")
            return

        # Тестовые заказы
        test_orders = [
            {
                "user_id": user.id,
                "service_id": 1,  # Генеральная уборка
                "params": json.dumps({
                    "meter": 50,
                    "date": "2025-09-24",
                    "time": "10:00",
                    "address": "ул. Ленина 1",
                    "extra_services": {"kitchen": 2, "fridge": 1}
                }),
                "total_price": 4600,  # 2000 + 50*50 + 800*2 + 800*1
                "status": "pending"
            },
            {
                "user_id": user.id,
                "service_id": 3,  # Уборка после ремонта
                "params": json.dumps({
                    "meter": 70,
                    "date": "2025-09-25",
                    "time": "14:30",
                    "address": "ул. Пушкина 10",
                    "extra_services": {"oven": 1}
                }),
                "total_price": 6500,  # 3000 + 70*70 + 800*1
                "status": "in_progress"
            },
            {
                "user_id": user.id,
                "service_id": 4,  # Мытьё окон
                "params": json.dumps({
                    "meter": 10,
                    "date": "2025-09-20",
                    "time": "12:00",
                    "address": "ул. Мира 5",
                    "extra_services": {}
                }),
                "total_price": 1500,  # 500 + 100*10
                "status": "completed"
            }
        ]

        for order_data in test_orders:
            if not db.query(Order).filter(Order.id == order_data.get("id")).first():
                order = Order(**order_data)
                db.add(order)
                print(f"Добавлен тестовый заказ: Услуга ID {order_data['service_id']}, Статус: {order_data['status']}")
        db.commit()
    except Exception as e:
        print(f"Ошибка при добавлении тестовых заказов: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_orders()