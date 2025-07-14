class SqlQueries:
    # Create all GTFS tables in correct order
    create_all_tables = """
    -- Independent tables first
    CREATE TABLE IF NOT EXISTS agency (
        agency_id TEXT PRIMARY KEY,
        agency_name TEXT NOT NULL,
        agency_url TEXT NOT NULL,
        agency_timezone TEXT NOT NULL,
        agency_lang TEXT,
        agency_fare_url TEXT
    );

    CREATE TABLE IF NOT EXISTS calendar (
        service_id TEXT PRIMARY KEY,
        monday INTEGER NOT NULL,
        tuesday INTEGER NOT NULL,
        wednesday INTEGER NOT NULL,
        thursday INTEGER NOT NULL,
        friday INTEGER NOT NULL,
        saturday INTEGER NOT NULL,
        sunday INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS calendar_dates (
        service_id TEXT NOT NULL,
        date TEXT NOT NULL,
        exception_type INTEGER NOT NULL,
        PRIMARY KEY (service_id, date)
    );

    CREATE TABLE IF NOT EXISTS stops (
        stop_id TEXT PRIMARY KEY,
        stop_name TEXT NOT NULL,
        stop_lat DECIMAL(10, 8),
        stop_lon DECIMAL(11, 8),
        location_type INTEGER DEFAULT 0,
        parent_station TEXT,
        platform_code TEXT
    );

    CREATE TABLE IF NOT EXISTS shapes (
        shape_id TEXT NOT NULL,
        shape_pt_lat DECIMAL(10, 8) NOT NULL,
        shape_pt_lon DECIMAL(11, 8) NOT NULL,
        shape_pt_sequence INTEGER NOT NULL,
        shape_dist_traveled DECIMAL(10, 2),
        PRIMARY KEY (shape_id, shape_pt_sequence)
    );

    CREATE TABLE IF NOT EXISTS feed_info (
        feed_id TEXT,
        feed_publisher_name TEXT NOT NULL,
        feed_publisher_url TEXT NOT NULL,
        feed_lang TEXT NOT NULL,
        feed_version TEXT
    );

    CREATE TABLE IF NOT EXISTS attributions (
        trip_id TEXT,
        organization_name TEXT NOT NULL,
        is_operator INTEGER
    );

    CREATE TABLE IF NOT EXISTS booking_rules (
        booking_rule_id TEXT PRIMARY KEY,
        booking_type INTEGER,
        prior_notice_duration_min INTEGER,
        prior_notice_last_day INTEGER,
        prior_notice_last_time TEXT,
        message TEXT,
        phone_number TEXT
    );

    -- Dependent tables
    CREATE TABLE IF NOT EXISTS routes (
        route_id TEXT PRIMARY KEY,
        agency_id TEXT NOT NULL,
        route_short_name TEXT,
        route_long_name TEXT,
        route_type INTEGER NOT NULL,
        route_desc TEXT,
        FOREIGN KEY (agency_id) REFERENCES agency(agency_id)
    );

    CREATE TABLE IF NOT EXISTS trips (
        route_id TEXT NOT NULL,
        service_id TEXT NOT NULL,
        trip_id TEXT PRIMARY KEY,
        trip_headsign TEXT,
        direction_id INTEGER,
        shape_id TEXT,
        FOREIGN KEY (route_id) REFERENCES routes(route_id)
    );

    CREATE TABLE IF NOT EXISTS stop_times (
        trip_id TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        stop_id TEXT NOT NULL,
        stop_sequence INTEGER NOT NULL,
        stop_headsign TEXT,
        pickup_type INTEGER DEFAULT 0,
        drop_off_type INTEGER DEFAULT 0,
        shape_dist_traveled DECIMAL(10, 2),
        timepoint INTEGER,
        pickup_booking_rule_id TEXT,
        drop_off_booking_rule_id TEXT,
        PRIMARY KEY (trip_id, stop_sequence),
        FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
        FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
    );

    """
    # Create indexes for better performance
    create_indexes = """
    CREATE INDEX IF NOT EXISTS idx_routes_agency_id ON routes(agency_id);
    CREATE INDEX IF NOT EXISTS idx_trips_route_id ON trips(route_id);
    CREATE INDEX IF NOT EXISTS idx_trips_service_id ON trips(service_id);
    CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id ON stop_times(trip_id);
    CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id ON stop_times(stop_id);
    CREATE INDEX IF NOT EXISTS idx_stop_times_sequence ON stop_times(stop_sequence);
    CREATE INDEX IF NOT EXISTS idx_shapes_shape_id ON shapes(shape_id);
    CREATE INDEX IF NOT EXISTS idx_calendar_dates_service_id ON calendar_dates(service_id);
    CREATE INDEX IF NOT EXISTS idx_calendar_dates_date ON calendar_dates(date);
    """

    # Cleanup queries
    truncate_all_tables = """
    TRUNCATE TABLE stop_times, trips, routes,
                   agency, stops, calendar, calendar_dates, shapes,
                   feed_info, attributions, booking_rules
    RESTART IDENTITY CASCADE;
    """

    drop_all_tables = """
    DROP TABLE IF EXISTS stop_times, trips, routes,
                         agency, stops, calendar, calendar_dates, shapes,
                         feed_info, attributions, booking_rules
    CASCADE;
    """
