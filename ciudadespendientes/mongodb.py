
middle_points_aggregate = [
    {'$match': {
        # 'year': 2023,
        'middlePoint': {'$exists': False}
        }
    },
    # {'$limit': 10},
    {'$unwind': '$geometry.coordinates'},
    {'$group': {
        '_id': '$_id',
        'midLat': {'$avg': {'$arrayElemAt': ['$geometry.coordinates', 0]}},
        'midLon': {'$avg': {'$arrayElemAt': ['$geometry.coordinates', 1]}}
        }
    },
    {'$project': {
        'middlePoint': {
            'type': 'Point',
            'coordinates': [
                {'$round': ['$midLat', 7]},
                {'$round': ['$midLon', 7]}
                ]
            }
        }
    }
]

points_inside = [
    {'$match': {
        'year': {'$in': '<yearsArray>'},
        'middlePoint': {
            '$geoIntersects': {
                '$geometry': {
                    'type': 'MultiPolygon',
                    'coordinates': '<city_bounds>'
                    }
                }
            }
        }
    },
    {'$group': {
        '_id': '$geometry.coordinates',
        'total_trip_count': {'$sum': '$total_trip_count'}
        }
    },
    {'$project': {
        '_id': 0,
        'coordinates': '$_id',
        'trips': '$total_trip_count'
        }
    }
]

points_inside_2 = [
    {'$match': {
        'year': {'$in': '<yearsArray>'},
        'osmId': { '$in': '<osmIdsArray>'}
        }
    },
    {
        '$project': '<projection>'
    },
    {'$group': {
        '_id': '$geometry',
        'total_trip_count': {'$sum': '$total_trip_count'}
        }
    }
]

map_middle_point = [
    {'$match': {
        'year': 2023,
        'middlePoint': {
            '$geoWithin': {
                '$geometry': {
                    'type': 'Polygon',
                    'coordinates': '<city_bounds>'
                    }
                }
            }
        }
    },
    {'$unwind': '$geometry.coordinates'},
    {'$group': {
        '_id': '',
        'midLat': {'$avg': {'$arrayElemAt': ['$geometry.coordinates', 0]}},
        'midLon': {'$avg': {'$arrayElemAt': ['$geometry.coordinates', 1]}}
        }
    },
    {'$project': {
        'middlePoint': {
            'type': 'Point',
            'coordinates': [
                {'$round': ['$midLat', 7]},
                {'$round': ['$midLon', 7]}
                ]
            }
        }
    }
]
