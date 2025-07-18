from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection
from core.database import metadata
from schemas.gtfs import RouteShape
from utils.transformers import transform_points_to_routes

async def get_all_shapes_by_route_name(conn: AsyncConnection, route_name: str) -> list[RouteShape]:
    routes = metadata.tables['routes']
    trips = metadata.tables['trips']
    shapes = metadata.tables['shapes']
    query = (
        select(
            trips.c.direction_id,
            trips.c.shape_id,
            shapes.c.shape_pt_lat,
            shapes.c.shape_pt_lon,
            shapes.c.shape_pt_sequence,
        ).distinct()
        .select_from(routes)
        .join(trips, routes.c.route_id == trips.c.route_id)
        .join(shapes, trips.c.shape_id == shapes.c.shape_id)
        .where(routes.c.route_short_name == route_name)
        .order_by(trips.c.shape_id, shapes.c.shape_pt_sequence)
    )

    result = await conn.execute(query)
    points = result.mappings().all()
    return transform_points_to_routes(points)
