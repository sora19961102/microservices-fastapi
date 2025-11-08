from typing import Union
import os
from dotenv import load_dotenv

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from redis_om import get_redis_connection, HashModel
from starlette.requests import Request

import requests

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = get_redis_connection(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str # pending, completed, refunded

    class Meta:
        database = redis

@app.post("/orders")
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    req = requests.get(f"http://localhost:8000/products/{body['id']}")
    product = req.json()
    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'],
        quantity=1,
        status='pending'
    )
    order.save()
    background_tasks.add_task(order_completed, order)

    return order

def order_completed(order: Order):
    order.status = 'completed'
    order.save()
