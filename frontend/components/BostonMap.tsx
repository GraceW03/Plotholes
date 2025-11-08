"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { renderToString } from "react-dom/server";
import { MapPin } from "lucide-react"; // any Lucide icon

// Create a custom DivIcon using Lucide SVG
const lucideMarkerIcon = L.divIcon({
  html: renderToString(<MapPin color="#2563eb" size={28} />), // Tailwind blue-600
  className: "lucide-marker", // we’ll style this below
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -25],
});

export default function BostonMap() {
  const center: [number, number] = [42.3601, -71.0589];

  return (
    <MapContainer
      center={center}
      zoom={12}
      style={{ height: "100vh", width: "100%" }}
      scrollWheelZoom
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      <Marker position={center} icon={lucideMarkerIcon}>
        <Popup>
          <div className="font-semibold">📍 Boston</div>
          <p className="text-sm text-zinc-600">Maphole base map running Lucide markers!</p>
        </Popup>
      </Marker>
    </MapContainer>
  );
}
