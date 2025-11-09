"use client";

import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapPin } from "lucide-react";
import { renderToString } from "react-dom/server";
import ReportDrawer from "@/components/ReportDrawer";

interface Report {
  UniqueKey: string;
  Latitude: number;
  Longitude: number;
  Status: string;
  Borough: string;
  Descriptor: string;
  CreatedDate: string;
}

/** Bridge component: grabs the real Leaflet map instance and hands it to a callback */
function MapRefBridge({ onInit }: { onInit: (map: L.Map) => void }) {
  const map = useMap();
  useEffect(() => {
    onInit(map);
  }, [map, onInit]);
  return null;
}

/** Keeps `selecting` live during leaflet click events */
function ClickHandler({
  selecting,
  onPick,
  onSelectingChange,
}: {
  selecting: boolean;
  onPick: (lat: number, lng: number) => void;
  onSelectingChange?: (v: boolean) => void;
}) {
  const map = useMap();
  const selectingRef = useRef(selecting);

  useEffect(() => {
    selectingRef.current = selecting;
    const el = map.getContainer();
    el.style.cursor = selecting ? "crosshair" : "";
    return () => {
      el.style.cursor = "";
    };
  }, [map, selecting]);

    useEffect(() => {
    const handleClick = (e: L.LeafletMouseEvent) => {
      if (!selectingRef.current) return;
      const { lat, lng } = e.latlng;
      onPick(lat, lng);
      onSelectingChange?.(false);
    };
    
    map.on("click", handleClick);
    
    // Cleanup function - just remove the event listener, don't return anything
    return () => {
      map.off("click", handleClick);
    };
  }, [map, onPick, onSelectingChange]);

  return null;
}

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

  const [reports, setReports] = useState<Report[]>([]);
  const [clickedCoords, setClickedCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [selecting, setSelecting] = useState(false);
  const mapRef = useRef<L.Map | null>(null);

  /** Lucide pin icon rendered as static HTML for Leaflet */
  const lucidePinHTML = renderToString(<MapPin size={26} color="#FF6B6B" />);
  const lucidePinIcon = L.divIcon({
    html: `<div style="transform: translate(-50%, -100%); display:flex;align-items:center;justify-content:center;">${lucidePinHTML}</div>`,
    className: "",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  });

  // Custom icons
  const lucideMarkerIcon = L.divIcon({
    html: renderToString(<MapPin size={24} color="#3B82F6" />),
    className: "",
    iconSize: [24, 24],
    iconAnchor: [12, 24]
  });

  /** Called when user clicks the map in select mode */
  const handlePick = (lat: number, lng: number) => {
    setClickedCoords({ lat, lng });
    setSelecting(false);
    mapRef.current?.flyTo([lat, lng], 15);
  };

  /** Called from drawer when "Select on map" clicked */
  const handleRequestSelect = () => {
    setSelecting(true);
    setClickedCoords(null);
  };

  /** Called when drawer geocodes or uses my location */
  const handleDropMarker = (lat: number, lng: number) => {
    setClickedCoords({ lat, lng });
    mapRef.current?.flyTo([lat, lng], 15);
  };
  const center: [number, number] = [40.7128, -74.0060]; // NYC coordinates
  const [route, setRoute] = useState<[number, number][]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Example origin/destination (you can make this dynamic)
  const origin: [number, number] = [40.681722, -73.832725];
  const destination: [number, number] = [40.682725, -73.829194];

  const fetchWithRetry = async (url: string, options = {}, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch(url, options);
        if (response.ok) return response;
        throw new Error(`HTTP error! status: ${response.status}`);
      } catch (error) {
        if (i === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
    throw new Error('Max retries reached');
  };

  const fetchOSRMRoute = async (start: [number, number], end: [number, number]) => {
    try {
      const [startLng, startLat] = [start[1], start[0]];
      const [endLng, endLat] = [end[1], end[0]];
      const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;
      
      const response = await fetchWithRetry(url);
      const data = await response.json();
      
      if (data.routes?.[0]?.geometry?.coordinates) {
        return data.routes[0].geometry.coordinates.map((coord: [number, number]) => [coord[1], coord[0]]);
      }
      throw new Error('Invalid route data format');
    } catch (error) {
      console.warn('Using fallback route due to:', error);
      // Return a simple straight line as fallback
      return [start, end];
    }
  };

  useEffect(() => {
    let isMounted = true;

    const fetchRoute = async () => {
      setIsLoading(true);
      try {
        const route = await fetchOSRMRoute(origin, destination);
        if (isMounted) {
          setRoute(route);
        }
      } catch (error) {
        console.error('Error in route fetching:', error);
        if (isMounted) {
          setRoute([origin, destination]);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchRoute();
    
    return () => {
      isMounted = false;
    };
  }, [origin, destination]);

  return (
    <div className="h-screen w-full relative bg-[#FFF9F3]">
      {isLoading && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white/90 px-4 py-2 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium">Loading route...</span>
        </div>
      )}
      <MapContainer
        center={[40.7128, -74.006]}
        zoom={11}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        {/* hand the real map instance to mapRef without whenCreated/whenReady */}
        <MapRefBridge onInit={(m) => (mapRef.current = m)} />

        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
        />

        {/* NYC Center Marker */}
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

        {/* Render existing pothole reports */}
        {reports.map((r) => (
          <CircleMarker
            key={r.UniqueKey}
            center={[r.Latitude, r.Longitude]}
            radius={4.5}
            pathOptions={{
              color:
                r.Status === "Closed" ? "#9bf6ff" :
                r.Status === "Open"   ? "#ffadad" :
                                       "#ffd6a5",
              fillOpacity: 0.9,
            }}
          >
            <Popup>
              <div className="text-sm font-medium leading-tight">
                <b>{r.Descriptor}</b><br />
                Status: {r.Status}<br />
                Borough: {r.Borough}<br />
                Created: {r.CreatedDate}
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Pin for selected or searched location */}
        {clickedCoords && (
          <Marker position={[clickedCoords.lat, clickedCoords.lng]} icon={lucidePinIcon}>
            <Popup>
              <div className="text-sm">
                📍 Selected Location
                <br />
                ({clickedCoords.lat.toFixed(4)}, {clickedCoords.lng.toFixed(4)})
              </div>
            </Popup>
          </Marker>
        )}

        <ClickHandler selecting={selecting} onPick={handlePick} onSelectingChange={setSelecting} />
      </MapContainer>

      {/* Header */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/80 backdrop-blur-md px-6 py-2 rounded-full text-sm sm:text-base font-semibold text-[#2B2B2B] shadow-md border border-[#f0f0f0]">
        🗽 NYC Pothole Reports •{' '}
        <span className="font-bold text-[#FF6B6B]">{reports.length}</span>{' '}
        {reports.length === 1 ? 'report' : 'reports'}
      </div>

      {/* Selection banner */}
      {selecting && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000] bg-[#FFD6A5] text-[#2B2B2B] px-4 py-2 rounded-full text-sm font-semibold shadow-md border border-[#f0e3c0]">
          👆 Click anywhere on the map to choose a location
        </div>
      )}

      {/* Drawer */}
      <ReportDrawer
        clickedCoords={clickedCoords}
        onDropMarker={handleDropMarker}
        onRequestSelect={handleRequestSelect}
      />
    </div>
  );
}
