"""Carrier compliance checking service.

For MVP, compliance is based on stored flags (authority_active, insurance_valid).
In production, this would integrate with FMCSA SAFER API and insurance verification services.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrier import Carrier
from app.models.load import EquipmentType


async def get_compliant_carriers(
    db: AsyncSession,
    equipment_type: EquipmentType,
    origin_state: str | None = None,
    destination_state: str | None = None,
    limit: int = 10,
) -> list[Carrier]:
    """Find carriers that are compliant and match the load requirements.

    Filters:
    1. is_compliant = True
    2. authority_active = True
    3. insurance_valid = True
    4. Equipment type matches (carrier supports the required equipment)
    5. Optionally filter by lane preference (origin/destination state)
    """
    query = select(Carrier).where(
        Carrier.is_compliant == True,  # noqa: E712
        Carrier.authority_active == True,  # noqa: E712
        Carrier.insurance_valid == True,  # noqa: E712
    )

    result = await db.execute(query)
    carriers = list(result.scalars().all())

    # Filter by equipment type in Python (JSON column)
    matching = []
    for carrier in carriers:
        equipment_list = carrier.equipment_types or []
        if equipment_type.value in equipment_list or not equipment_list:
            # If lane preferences exist, check them
            if origin_state and destination_state and carrier.lanes:
                for lane in carrier.lanes:
                    if (
                        lane.get("origin_state") == origin_state
                        and lane.get("destination_state") == destination_state
                    ):
                        matching.append(carrier)
                        break
            else:
                matching.append(carrier)

        if len(matching) >= limit:
            break

    return matching


def check_carrier_compliance(carrier: Carrier) -> tuple[bool, list[str]]:
    """Check a single carrier's compliance status.

    Returns (is_compliant, list_of_issues).
    """
    issues = []
    if not carrier.authority_active:
        issues.append("FMCSA authority is not active")
    if not carrier.insurance_valid:
        issues.append("Insurance is expired or invalid")
    if not carrier.is_compliant:
        issues.append("Carrier flagged as non-compliant")

    return len(issues) == 0, issues
