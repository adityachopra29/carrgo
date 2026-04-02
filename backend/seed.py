"""Seed the database with sample carriers for development."""

import asyncio

from app.database import async_session, init_db
from app.models.carrier import Carrier

SAMPLE_CARRIERS = [
    {
        "name": "Midwest Express Freight",
        "mc_number": "MC-100001",
        "dot_number": "DOT-200001",
        "phone": "+15551000001",
        "email": "dispatch@midwestexpress.example.com",
        "equipment_types": ["dry_van", "reefer"],
        "lanes": [
            {"origin_state": "IL", "destination_state": "GA"},
            {"origin_state": "IL", "destination_state": "OH"},
            {"origin_state": "IN", "destination_state": "TX"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "Southern Haulers Inc",
        "mc_number": "MC-100002",
        "dot_number": "DOT-200002",
        "phone": "+15551000002",
        "email": "ops@southernhaulers.example.com",
        "equipment_types": ["dry_van", "flatbed"],
        "lanes": [
            {"origin_state": "GA", "destination_state": "FL"},
            {"origin_state": "IL", "destination_state": "GA"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "Pacific Coast Transport",
        "mc_number": "MC-100003",
        "dot_number": "DOT-200003",
        "phone": "+15551000003",
        "email": "dispatch@pacificcoast.example.com",
        "equipment_types": ["reefer", "dry_van"],
        "lanes": [
            {"origin_state": "CA", "destination_state": "WA"},
            {"origin_state": "CA", "destination_state": "OR"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "Lone Star Logistics",
        "mc_number": "MC-100004",
        "dot_number": "DOT-200004",
        "phone": "+15551000004",
        "email": "booking@lonestar.example.com",
        "equipment_types": ["flatbed", "step_deck", "dry_van"],
        "lanes": [
            {"origin_state": "TX", "destination_state": "IL"},
            {"origin_state": "TX", "destination_state": "CA"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "Great Lakes Carriers",
        "mc_number": "MC-100005",
        "dot_number": "DOT-200005",
        "phone": "+15551000005",
        "email": "dispatch@greatlakes.example.com",
        "equipment_types": ["dry_van"],
        "lanes": [
            {"origin_state": "MI", "destination_state": "OH"},
            {"origin_state": "IL", "destination_state": "IN"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "Rocky Mountain Freight",
        "mc_number": "MC-100006",
        "dot_number": "DOT-200006",
        "phone": "+15551000006",
        "email": "ops@rockymtn.example.com",
        "equipment_types": ["dry_van", "reefer", "flatbed"],
        "lanes": [
            {"origin_state": "CO", "destination_state": "UT"},
            {"origin_state": "CO", "destination_state": "KS"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "East Coast Express",
        "mc_number": "MC-100007",
        "dot_number": "DOT-200007",
        "phone": "+15551000007",
        "email": "dispatch@eastcoastexp.example.com",
        "equipment_types": ["dry_van", "reefer"],
        "lanes": [
            {"origin_state": "NJ", "destination_state": "FL"},
            {"origin_state": "NY", "destination_state": "PA"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        "name": "Delta Trucking Co",
        "mc_number": "MC-100008",
        "dot_number": "DOT-200008",
        "phone": "+15551000008",
        "email": "dispatch@deltatrucking.example.com",
        "equipment_types": ["dry_van"],
        "lanes": [
            {"origin_state": "IL", "destination_state": "GA"},
            {"origin_state": "TN", "destination_state": "GA"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
    {
        # Non-compliant carrier for testing compliance filtering
        "name": "Questionable Freight LLC",
        "mc_number": "MC-100009",
        "dot_number": "DOT-200009",
        "phone": "+15551000009",
        "email": "info@questionable.example.com",
        "equipment_types": ["dry_van"],
        "lanes": [
            {"origin_state": "IL", "destination_state": "GA"},
        ],
        "is_compliant": False,
        "authority_active": False,
        "insurance_valid": False,
    },
    {
        "name": "Heartland Hauling",
        "mc_number": "MC-100010",
        "dot_number": "DOT-200010",
        "phone": "+15551000010",
        "email": "dispatch@heartland.example.com",
        "equipment_types": ["dry_van", "reefer", "flatbed", "step_deck"],
        "lanes": [
            {"origin_state": "IL", "destination_state": "GA"},
            {"origin_state": "MO", "destination_state": "TX"},
            {"origin_state": "KS", "destination_state": "CO"},
        ],
        "is_compliant": True,
        "authority_active": True,
        "insurance_valid": True,
    },
]


async def seed():
    await init_db()

    async with async_session() as db:
        from sqlalchemy import select, func

        result = await db.execute(select(func.count(Carrier.id)))
        count = result.scalar()
        if count and count > 0:
            print(f"Database already has {count} carriers. Skipping seed.")
            return

        for data in SAMPLE_CARRIERS:
            carrier = Carrier(**data)
            db.add(carrier)

        await db.commit()
        print(f"Seeded {len(SAMPLE_CARRIERS)} carriers.")


if __name__ == "__main__":
    asyncio.run(seed())
