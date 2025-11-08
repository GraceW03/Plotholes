"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { renderToString } from "react-dom/server";
import { MapPin } from "lucide-react";

// Create a custom DivIcon using Lucide SVG
const lucideMarkerIcon = L.divIcon({
  html: renderToString(<MapPin color="#ef4444" size={28} />), // Using red color for NYC
  className: "lucide-marker",
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -25],
});

export default function NYCMap() {
  const center: [number, number] = [40.7128, -74.0060]; // NYC coordinates

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
          <div className="font-semibold">📍 New York City</div>
          <p className="text-sm text-zinc-600">NYC map with custom marker</p>
        </Popup>
      </Marker>
    </MapContainer>
  );
}