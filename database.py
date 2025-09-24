import os
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///cleaning_bot.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    points = Column(Integer, default=0)
    orders = relationship("Order", back_populates="user")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    base_price = Column(Float)
    price_per_meter = Column(Float)
    description = Column(String)
    orders = relationship("Order", back_populates="service")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    params = Column(JSON)
    total_price = Column(Float)
    status = Column(String, default="pending")  # pending, in_progress, completed
    user = relationship("User", back_populates="orders")
    service = relationship("Service", back_populates="orders")

def init_db():
    print("Инициализация базы данных...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        services = [
            {"name": "Генеральная уборка", "base_price": 2000, "price_per_meter": 50, "description": "Полная уборка помещений"},
            {"name": "Поддерживающая уборка", "base_price": 1000, "price_per_meter": 30, "description": "Лёгкая уборка помещений"},
            {"name": "Уборка после ремонта", "base_price": 3000, "price_per_meter": 70, "description": "Уборка после строительных работ"},
            {"name": "Мытьё окон", "base_price": 500, "price_per_meter": 100, "description": "Мытьё окон и рам"}
        ]
        for service in services:
            if not db.query(Service).filter(Service.name == service["name"]).first():
                db_service = Service(**service)
                db.add(db_service)
                print(f"Добавлена услуга: {service['name']}")
        db.commit()
    except Exception as e:
        print(f"Ошибка при добавлении услуг: {str(e)}")
        db.rollback()
    finally:
        db.close()

def get_user(telegram_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, points=0)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()

def get_services():
    db = SessionLocal()
    try:
        return db.query(Service).all()
    finally:
        db.close()

def get_user_orders(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Order).filter(Order.user_id == user_id).all()
    finally:
        db.close()

def get_all_orders():
    db = SessionLocal()
    try:
        return db.query(Order).all()
    finally:
        db.close()

def create_order(user_id: int, service_id: int, params: str, total_price: float):
    db = SessionLocal()
    try:
        order = Order(user_id=user_id, service_id=service_id, params=params, total_price=total_price, status="pending")
        db.add(order)
        db.commit()
        db.refresh(order)
        return order.id
    except Exception as e:
        print(f"Ошибка при создании заказа: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()