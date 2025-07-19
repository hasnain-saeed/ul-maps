export const UPPSALA_COORDINATES: [number, number] = [17.6389, 59.8586];
export const INITIAL_ZOOM = 10;
export const MAP_STYLE_URL = '/style.json';

export const MAP_CONFIG = {
  minZoom: 5,
  maxZoom: 20,
} as const;

export const VEHICLE_LAYER_CONFIG = {
  iconSize: 0.8,
  iconAllowOverlap: true,
  iconRotationAlignment: 'map',
} as const;