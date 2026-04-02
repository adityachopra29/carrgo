"""Server-Sent Events endpoint for real-time updates."""

import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.events import event_manager

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/{load_id}")
async def stream_load_events(load_id: str):
    """SSE endpoint that streams real-time updates for a specific load.

    The frontend connects to this endpoint with EventSource and receives
    events as calls progress, quotes come in, and campaign status changes.
    """

    async def event_generator():
        queue = event_manager.subscribe(load_id)
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {{\"load_id\": \"{load_id}\"}}\n\n"

            while True:
                try:
                    # Wait for events with a timeout for keepalive
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_manager.unsubscribe(load_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
