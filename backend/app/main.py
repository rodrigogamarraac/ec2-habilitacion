from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="LOUD Tickets API",
    description="Project A backend for concert ticketing with capacity enforcement.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TicketType = Literal["general", "vip", "backstage"]


class TicketTier(BaseModel):
    type: TicketType
    label: str
    price: float
    capacity: int
    sold: int = 0

    @property
    def available(self) -> int:
        return self.capacity - self.sold


class Event(BaseModel):
    id: str
    name: str
    artist: str
    venue: str
    city: str
    starts_at: datetime
    description: str
    tiers: Dict[TicketType, TicketTier]


class EventSummary(BaseModel):
    id: str
    name: str
    artist: str
    venue: str
    city: str
    starts_at: datetime
    total_capacity: int
    total_sold: int
    available: int
    sold_out: bool
    min_price: float


class TicketTierResponse(BaseModel):
    type: TicketType
    label: str
    price: float
    capacity: int
    sold: int
    available: int


class EventDetail(BaseModel):
    id: str
    name: str
    artist: str
    venue: str
    city: str
    starts_at: datetime
    description: str
    tiers: List[TicketTierResponse]
    available: int
    sold_out: bool


class PurchaseRequest(BaseModel):
    event_id: str = Field(..., examples=["neon-nights"])
    ticket_type: TicketType = Field(..., examples=["general"])
    quantity: int = Field(..., ge=1, le=10)
    customer_name: str = Field(..., min_length=2)
    customer_email: EmailStr


class PurchaseResponse(BaseModel):
    order_id: str
    event_id: str
    ticket_type: TicketType
    quantity: int
    unit_price: float
    total: float
    remaining: int
    status: str


inventory_lock = Lock()
orders: Dict[str, PurchaseResponse] = {}

EVENTS: Dict[str, Event] = {
    "neon-nights": Event(
        id="neon-nights",
        name="Neon Nights Festival",
        artist="The Midnight Echoes",
        venue="Estadio Real Santa Cruz",
        city="Santa Cruz",
        starts_at=datetime(2026, 8, 15, 20, 30, tzinfo=timezone.utc),
        description="A synth-pop concert experience with lights, visuals and live bands.",
        tiers={
            "general": TicketTier(type="general", label="General", price=120, capacity=250, sold=42),
            "vip": TicketTier(type="vip", label="VIP", price=250, capacity=80, sold=18),
            "backstage": TicketTier(type="backstage", label="Backstage", price=500, capacity=20, sold=5),
        },
    ),
    "andes-rock": Event(
        id="andes-rock",
        name="Andes Rock Live",
        artist="Altiplano Sound",
        venue="Teatro al Aire Libre",
        city="La Paz",
        starts_at=datetime(2026, 9, 5, 19, 0, tzinfo=timezone.utc),
        description="Rock latino with Andean fusion and special guests.",
        tiers={
            "general": TicketTier(type="general", label="General", price=90, capacity=200, sold=61),
            "vip": TicketTier(type="vip", label="VIP", price=180, capacity=60, sold=12),
            "backstage": TicketTier(type="backstage", label="Backstage", price=420, capacity=15, sold=6),
        },
    ),
    "acoustic-sunset": Event(
        id="acoustic-sunset",
        name="Acoustic Sunset Sessions",
        artist="Marina & The Pines",
        venue="Centro Cultural",
        city="Cochabamba",
        starts_at=datetime(2026, 7, 10, 18, 30, tzinfo=timezone.utc),
        description="An intimate acoustic show for a limited audience.",
        tiers={
            "general": TicketTier(type="general", label="General", price=70, capacity=100, sold=100),
            "vip": TicketTier(type="vip", label="VIP", price=150, capacity=25, sold=25),
            "backstage": TicketTier(type="backstage", label="Backstage", price=300, capacity=5, sold=5),
        },
    ),
}


def build_summary(event: Event) -> EventSummary:
    total_capacity = sum(tier.capacity for tier in event.tiers.values())
    total_sold = sum(tier.sold for tier in event.tiers.values())
    available = total_capacity - total_sold
    return EventSummary(
        id=event.id,
        name=event.name,
        artist=event.artist,
        venue=event.venue,
        city=event.city,
        starts_at=event.starts_at,
        total_capacity=total_capacity,
        total_sold=total_sold,
        available=available,
        sold_out=available == 0,
        min_price=min(tier.price for tier in event.tiers.values()),
    )


def build_detail(event: Event) -> EventDetail:
    tiers = [
        TicketTierResponse(
            type=tier.type,
            label=tier.label,
            price=tier.price,
            capacity=tier.capacity,
            sold=tier.sold,
            available=tier.available,
        )
        for tier in event.tiers.values()
    ]
    available = sum(tier.available for tier in event.tiers.values())
    return EventDetail(
        id=event.id,
        name=event.name,
        artist=event.artist,
        venue=event.venue,
        city=event.city,
        starts_at=event.starts_at,
        description=event.description,
        tiers=tiers,
        available=available,
        sold_out=available == 0,
    )


@app.get("/api/v1/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "loud-tickets-api"}


@app.get("/api/v1/events", response_model=list[EventSummary])
def list_events(
    city: Optional[str] = Query(default=None),
    only_available: bool = Query(default=False),
) -> list[EventSummary]:
    results = [build_summary(event) for event in EVENTS.values()]
    if city:
        results = [event for event in results if event.city.lower() == city.lower()]
    if only_available:
        results = [event for event in results if event.available > 0]
    return sorted(results, key=lambda event: event.starts_at)


@app.get("/api/v1/events/{event_id}", response_model=EventDetail)
def get_event(event_id: str) -> EventDetail:
    event = EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return build_detail(event)


@app.post("/api/v1/orders", response_model=PurchaseResponse, status_code=201)
def create_order(payload: PurchaseRequest) -> PurchaseResponse:
    with inventory_lock:
        event = EVENTS.get(payload.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        tier = event.tiers.get(payload.ticket_type)
        if not tier:
            raise HTTPException(status_code=404, detail="Ticket type not found")

        if tier.available < payload.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Not enough tickets available. Remaining: {tier.available}",
            )

        tier.sold += payload.quantity
        order = PurchaseResponse(
            order_id=str(uuid4()),
            event_id=event.id,
            ticket_type=tier.type,
            quantity=payload.quantity,
            unit_price=tier.price,
            total=tier.price * payload.quantity,
            remaining=tier.available,
            status="confirmed",
        )
        orders[order.order_id] = order
        return order


@app.get("/api/v1/orders/{order_id}", response_model=PurchaseResponse)
def get_order(order_id: str) -> PurchaseResponse:
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# Compatibility aliases for possible frontend naming variants.
@app.get("/api/v1/concerts", response_model=list[EventSummary])
def list_concerts() -> list[EventSummary]:
    return list_events()


@app.get("/api/v1/concerts/{event_id}", response_model=EventDetail)
def get_concert(event_id: str) -> EventDetail:
    return get_event(event_id)


@app.post("/api/v1/tickets", response_model=PurchaseResponse, status_code=201)
def buy_tickets(payload: PurchaseRequest) -> PurchaseResponse:
    return create_order(payload)


@app.post("/api/v1/purchases", response_model=PurchaseResponse, status_code=201)
def create_purchase(payload: PurchaseRequest) -> PurchaseResponse:
    return create_order(payload)
