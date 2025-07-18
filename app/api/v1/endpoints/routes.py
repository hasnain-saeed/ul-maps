from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection
from core.database import get_async_connection
from crud.routes import get_all_shapes_by_route_name
from schemas.gtfs import RouteShape

router = APIRouter()

@router.get(
    "/routes/{route_name}/shape",
    response_model=list[RouteShape]
)
async def get_route_shape_endpoint(
    route_name: str,
    conn: AsyncConnection = Depends(get_async_connection)
):
    """
    API endpoint to get the shapes for a given route.
    This endpoint returns a JSON array of shape points.
    """
    validated_shapes = await get_all_shapes_by_route_name(conn, route_name)
    return validated_shapes
