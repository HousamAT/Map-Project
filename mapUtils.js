// mapUtils.js
export function addMarker(map, lat, lng) {
    const latlng = [lat, lng];
    L.marker(latlng).addTo(map);
}