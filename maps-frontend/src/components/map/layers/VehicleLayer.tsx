import { useEffect } from 'react';
import type { Map as MapLibreMap, GeoJSONSource } from 'maplibre-gl';
import maplibregl from 'maplibre-gl';
import type { Feature, Point } from 'geojson';
import { createCircularTextIcon } from '../utils/iconHelpers';
import { VEHICLE_LAYER_CONFIG } from '../utils/constants';
import type { VehiclePosition } from '../../../realtime/types/messages';

interface VehicleProperties {
  id: string;
  trip_id: string;
  speed: number;
  bearing: number;
  timestamp: number;
}

interface VehicleLayerProps {
  map: MapLibreMap;
  vehiclePositions: Map<string, VehiclePosition>;
  isMapLoaded: boolean;
}

export const VehicleLayer = ({ map, vehiclePositions, isMapLoaded }: VehicleLayerProps) => {

  // Initialize vehicle layer
  useEffect(() => {
    if (!isMapLoaded) return;

    const busIcon = createCircularTextIcon('B');
    map.addImage('bus-icon', busIcon, { sdf: false });

    map.addSource('vehicles', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: [],
      },
    });

    map.addLayer({
      id: 'vehicle-markers',
      type: 'symbol',
      source: 'vehicles',
      layout: {
        'icon-image': 'bus-icon',
        'icon-size': VEHICLE_LAYER_CONFIG.iconSize,
        'icon-allow-overlap': VEHICLE_LAYER_CONFIG.iconAllowOverlap,
        'icon-rotation-alignment': VEHICLE_LAYER_CONFIG.iconRotationAlignment,
      },
    });

    // Add click handler for vehicle popups
    map.on('click', 'vehicle-markers', (e) => {
      if (!e.features?.[0]) return;

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
        .addTo(map);
    });

    // Add hover effects
    map.on('mouseenter', 'vehicle-markers', () => {
      map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'vehicle-markers', () => {
      map.getCanvas().style.cursor = '';
    });

    return () => {
      if (map.getLayer('vehicle-markers')) {
        map.removeLayer('vehicle-markers');
      }
      if (map.getSource('vehicles')) {
        map.removeSource('vehicles');
      }
    };
  }, [map, isMapLoaded]);

  // Update vehicle positions
  useEffect(() => {
    if (!isMapLoaded || vehiclePositions.size === 0) {
      return;
    }

    const vehiclesSource = map.getSource('vehicles') as GeoJSONSource | undefined;
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
  }, [vehiclePositions, isMapLoaded, map]);

  return null;
};
