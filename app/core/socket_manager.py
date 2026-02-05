from typing import List, Dict, Any
from fastapi import WebSocket
import json
import asyncio
from app.core.logger import get_logger

logger = get_logger(__name__)


class SocketManager:
    """
    Manages WebSocket connections for real-time updates.
    """

    def __init__(self):
        # Map project_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        logger.info(
            f"WebSocket connected for project {project_id}. Total: {len(self.active_connections[project_id])}"
        )

    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
                logger.info(f"WebSocket disconnected for project {project_id}")
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def broadcast(self, project_id: str, message: Dict[str, Any]):
        """
        Broadcasts a JSON message to all connected clients for a given project.
        """
        if project_id in self.active_connections:
            # Create snapshot to avoid modification during iteration
            connections = self.active_connections[project_id][:]

            logger.debug(
                f"Broadcasting to {len(connections)} clients in project {project_id}: {message.get('type')}"
            )

            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message: {e}")
                    # Likely disconnected, cleanup
                    self.disconnect(connection, project_id)


# Global instance
manager = SocketManager()
