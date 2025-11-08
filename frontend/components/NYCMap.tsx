"use client";

import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
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

// Component to automatically fit map to route
function FitBounds({ route }: { route: [number, number][] }) {
  const map = useMap();

  useEffect(() => {
    if (route.length > 0) {
      const bounds = L.latLngBounds(route); // creates bounds that encompass all route points
      map.fitBounds(bounds, { padding: [50, 50] }); // add padding so markers aren't at the edge
    }
  }, [route, map]);

  return null;
}

export default function NYCMap() {
  const center: [number, number] = [40.7128, -74.0060]; // NYC coordinates
  const [route, setRoute] = useState<[number, number][]>([]);

  // Example origin/destination (you can make this dynamic)
  const origin: [number, number] = [40.681722, -73.832725];
  const destination: [number, number] = [40.682725, -73.829194];

  useEffect(() => {
    const fetchRoute = async () => {
      try {
        const response = await fetch("http://localhost:3001/api/route", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ origin, destination }),
        });

        if (!response.ok) throw new Error("Failed to fetch route");

        const data = await response.json();
        setRoute(data.route); // route is an array of [lat, lon] pairs
      } catch (err) {
        console.error(err);
      }
    };

    fetchRoute();
  }, []);

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

      {/* Origin marker */}
      <Marker position={origin} icon={lucideMarkerIcon}>
        <Popup>Origin</Popup>
      </Marker>

      {/* Destination marker */}
      <Marker position={destination} icon={lucideMarkerIcon}>
        <Popup>Destination</Popup>
      </Marker>

      {/* Route Polyline */}
      {route.length > 0 && (
        <Polyline positions={route} color="red" weight={4} />
      )}

      {/* Fit map to route */}
      <FitBounds route={route} />
    </MapContainer>
  );
}