from typing import List, Optional, Tuple
from sqlmodel import select, col, case
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.tree_node import TreeNode
from .base_repository import BaseRepository


class TreeNodeRepository(BaseRepository[TreeNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(TreeNode, session)

    async def get_node(self, project_id: str, path: str) -> Optional[TreeNode]:
        """Get a specific node by project and path (Composite Key)."""
        return await self.session.get(TreeNode, (project_id, path))

    async def get_pending_nodes(
        self, project_id: str, limit: int = 10
    ) -> List[TreeNode]:
        """
        Get pending nodes ordered by priority: high > medium > low.
        """
        # Define priority order using a CASE statement
        priority_order = case(
            (TreeNode.priority == "high", 1),
            (TreeNode.priority == "medium", 2),
            (TreeNode.priority == "low", 3),
            else_=4,
        )

        statement = (
            select(TreeNode)
            .where(TreeNode.project_id == project_id)
            .where(TreeNode.status == "pending")
            .order_by(priority_order)
            .limit(limit)
        )

        results = await self.session.exec(statement)
        return results.all()

    async def get_project_tree(self, project_id: str) -> List[TreeNode]:
        """Get all nodes for a project."""
        statement = select(TreeNode).where(TreeNode.project_id == project_id)
        results = await self.session.exec(statement)
        return results.all()
