"""SSE event manager for real-time updates to the frontend."""

import asyncio
import json
from collections import defaultdict


class EventManager:
    """Manages SSE event streams per load_id.

    Each active load detail page subscribes to events for that load.
    When a call status changes or a quote comes in, we push an event.
    """

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, load_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[load_id].append(queue)
        return queue

    def unsubscribe(self, load_id: str, queue: asyncio.Queue):
        if load_id in self._subscribers:
            self._subscribers[load_id] = [
                q for q in self._subscribers[load_id] if q is not queue
            ]
            if not self._subscribers[load_id]:
                del self._subscribers[load_id]

    async def publish(self, load_id: str, event_type: str, data: dict):
        payload = json.dumps({"type": event_type, "data": data})
        for queue in self._subscribers.get(load_id, []):
            await queue.put(payload)

    async def publish_call_update(self, load_id: str, call_data: dict):
        await self.publish(load_id, "call_update", call_data)

    async def publish_campaign_update(self, load_id: str, campaign_data: dict):
        await self.publish(load_id, "campaign_update", campaign_data)

    async def publish_quote(self, load_id: str, quote_data: dict):
        await self.publish(load_id, "new_quote", quote_data)


# Singleton
event_manager = EventManager()
