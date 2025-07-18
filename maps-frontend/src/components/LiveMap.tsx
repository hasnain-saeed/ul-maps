import { useEffect, useRef, useState } from 'react';
import maplibregl, { Map as MapLibreMap, GeoJSONSource } from 'maplibre-gl';
import type { Feature, Point } from 'geojson';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useVehicles, type VehiclePosition } from '../hooks/useVehicles';

const UPPSALA_COORDINATES: [number, number] = [17.6389, 59.8586];
const INITIAL_ZOOM = 10;
const MAP_STYLE_URL = '/style.json';

const createCircularTextIcon = (
  text: string,
  options: {
    size?: number;
    backgroundColor?: string;
    textColor?: string;
    font?: string;
  } = {}
): ImageData => {
  const {
    size = 32,
    backgroundColor = '#dfa32a',
    textColor = '#ffffff',
    font = `bold ${size * 0.5}px Arial`,
  } = options;

  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = backgroundColor;
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2, 0, 2 * Math.PI);
  ctx.fill();

  ctx.fillStyle = textColor;
  ctx.font = font;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, size / 2, size / 2 + 1); // +1 for better vertical centering

  return ctx.getImageData(0, 0, size, size);
};

interface VehicleProperties {
  id: string;
  trip_id: string;
  speed: number;
  bearing: number;
  timestamp: number;
}

const LiveMap = () => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  // Get live data from our custom hook
  const { vehiclePositions, isLoading, isError } = useVehicles();

  // Effect for initializing the map (runs only once)
  useEffect(() => {
    if (map.current || !mapContainer.current) return; // Exit if map is already initialized or container not ready

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE_URL,
      center: UPPSALA_COORDINATES,
      zoom: INITIAL_ZOOM,
      minZoom: 5,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      if (!map.current) return;

      const busIcon = createCircularTextIcon('B');
      map.current.addImage('bus-icon', busIcon, { sdf: false });

      map.current.addSource('vehicles', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [],
        },
      });

      map.current.addLayer({
        id: 'vehicle-markers',
        type: 'symbol',
        source: 'vehicles',
        layout: {
          'icon-image': 'bus-icon',
          'icon-size': 0.8,
          'icon-allow-overlap': true,
          'icon-rotation-alignment': 'map',
        },
      });

      map.current.on('click', 'vehicle-markers', (e) => {
        if (!e.features?.[0] || !map.current) return;

        const feature = e.features[0];
        const coordinates = (feature.geometry as Point).coordinates.slice() as [number, number];
        const { id, trip_id, speed, timestamp } = feature.properties as VehicleProperties;

        const speedKmh = (speed * 3.6).toFixed(1);
        const lastUpdate = new Date(timestamp * 1000).toLocaleTimeString();

        new maplibregl.Popup()
          .setLngLat(coordinates)
          .setHTML(`
            <h3>Vehicle ${id}</h3>
            <p><strong>Trip:</strong> ${trip_id || 'N/A'}</p>
            <p><strong>Speed:</strong> ${speedKmh} km/h</p>
            <p><strong>Updated:</strong> ${lastUpdate}</p>
          `)
          .addTo(map.current);
      });

      map.current.on('mouseenter', 'vehicle-markers', () => map.current!.getCanvas().style.cursor = 'pointer');
      map.current.on('mouseleave', 'vehicle-markers', () => map.current!.getCanvas().style.cursor = '');
      setIsMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    if (!isMapLoaded || !vehiclePositions || vehiclePositions.size === 0) {
      return;
    }

    const vehiclesSource = map.current?.getSource('vehicles') as GeoJSONSource | undefined;
    if (!vehiclesSource) return;

    const features: Feature<Point, VehicleProperties>[] = Array.from(vehiclePositions.values())
      .map((vehicle: VehiclePosition) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [vehicle.longitude, vehicle.latitude],
        },
        properties: {
          id: vehicle.vehicle_id,
          bearing: vehicle.bearing || 0,
          speed: vehicle.speed || 0,
          trip_id: vehicle.trip_id || 'N/A',
          timestamp: vehicle.timestamp || Date.now() / 1000,
        },
      }));

    vehiclesSource.setData({
      type: 'FeatureCollection',
      features,
    });
  }, [vehiclePositions, isMapLoaded]);

  return (
    <div className="map-container">
      <div className="status-bar">
        {isLoading && <span className="status loading">🟡 Loading vehicles...</span>}
        {isError && <span className="status disconnected">🔴 Error fetching data</span>}
        {vehiclePositions && <span className="status connected">🟢 Connected</span>}
        <span className="vehicle-count">
          Vehicles: {vehiclePositions?.size || 0}
        </span>
      </div>
      <div ref={mapContainer} className="map" />
    </div>
  );
};

export default LiveMap;
