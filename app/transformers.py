
import itertools
import operator
import schemas

def transform_points_to_routes(points) -> list[schemas.RouteShape]:

    aggregated_list = []

    for shape_id, group_iterator in itertools.groupby(points, key=operator.attrgetter('shape_id')):
        points_in_group = list(group_iterator)
        first_point = points_in_group[0]

        coords = [[p.shape_pt_lon, p.shape_pt_lat] for p in points_in_group]
        aggregated_list.append(
            schemas.RouteShape(
                direction_id=first_point.direction_id,
                shape_id=shape_id,
                coordinates=coords
            )
        )

    return aggregated_list
