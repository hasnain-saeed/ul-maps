import { useEffect, useRef, useState } from 'react';
import maplibregl, { Map as MapLibreMap } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useVehicleContext } from '../context/VehicleContext';
import { VehicleLayer } from './map/layers';
import { UPPSALA_COORDINATES, INITIAL_ZOOM, MAP_STYLE_URL, MAP_CONFIG } from './map/utils/constants';

const LiveMap = () => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const { vehiclePositions, isLoading, isError } = useVehicleContext();

  // Initialize map
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE_URL,
      center: UPPSALA_COORDINATES,
      zoom: INITIAL_ZOOM,
      minZoom: MAP_CONFIG.minZoom,
      maxZoom: MAP_CONFIG.maxZoom,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      setIsMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

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
      {map.current && vehiclePositions && (
        <VehicleLayer
          map={map.current}
          vehiclePositions={vehiclePositions}
          isMapLoaded={isMapLoaded}
        />
      )}
    </div>
  );
};

export default LiveMap;
