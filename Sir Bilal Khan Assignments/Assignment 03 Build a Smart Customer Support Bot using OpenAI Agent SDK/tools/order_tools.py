from openai import function_tool
import random

# Mock order database
ORDERS = {
    "123": "Shipped",
    "456": "Processing",
    "789": "Delivered"
}

@function_tool(
    name="get_order_status",
    description="Fetch the status of a customer's order by order_id",
    is_enabled=lambda query: "order" in query.lower(),   # only enabled when 'order' mentioned
    error_function=lambda e: f"Sorry, couldn't fetch order. Error: {str(e)}"
)
def get_order_status(order_id: str) -> str:
    """Simulates fetching order status"""
    if order_id not in ORDERS:
        raise ValueError("Order ID not found. Please check and try again.")
    return f"Order {order_id} is currently {ORDERS[order_id]}."
