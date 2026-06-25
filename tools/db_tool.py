import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "../database/fraud_detector.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_user_history(user_id: str) -> dict:
    """
    Fetch user history from DB for the last 30 days.
    Returns refund_count, total_orders, refund_ratio, account_age_days.
    Used by Intake Agent to populate FraudState.
    """
    conn = get_connection()
    cursor = conn.cursor()

    
    cursor.execute("""
        SELECT account_age_days FROM users WHERE user_id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {
            "found": False,
            "user_id": user_id,
            "account_age_days": None,
            "total_orders": None,
            "refund_count_30days": None,
            "refund_ratio_30days": None,
        }

    account_age_days = user[0]

    
    cursor.execute("""
        SELECT COUNT(*) FROM orders WHERE user_id = ?
    """, (user_id,))
    total_orders = cursor.fetchone()[0]

    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COUNT(*) FROM refunds
        WHERE user_id = ?
        AND refund_date >= ?
    """, (user_id, thirty_days_ago))
    refund_count_30days = cursor.fetchone()[0]


    if total_orders > 0:
        refund_ratio_30days = round(refund_count_30days / total_orders, 2)
    else:
        refund_ratio_30days = 0.0

    conn.close()

    return {
        "found": True,
        "user_id": user_id,
        "account_age_days": account_age_days,
        "total_orders": total_orders,
        "refund_count_30days": refund_count_30days,
        "refund_ratio_30days": refund_ratio_30days,
    }


def get_order_details(order_id: str) -> dict:
    """
    Fetch order details from DB.
    Used by Intake Agent to verify order exists and get food item.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT order_id, user_id, food_item, order_date, amount
        FROM orders WHERE order_id = ?
    """, (order_id,))

    order = cursor.fetchone()
    conn.close()

    if not order:
        return {
            "found": False,
            "order_id": order_id,
        }

    return {
        "found": True,
        "order_id": order[0],
        "user_id": order[1],
        "food_item": order[2],
        "order_date": order[3],
        "amount": order[4],
    }