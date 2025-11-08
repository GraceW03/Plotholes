"use client";

import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
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

export default function NYCMap() {
  const [reports, setReports] = useState<Report[]>([]);
  const [clickedCoords, setClickedCoords] = useState<{ lat: number; lng: number } | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  // load pothole data
  useEffect(() => {
    fetch("/data/nyc_potholes.geojson")
      .then((res) => res.json())
      .then((data) => setReports(data))
      .catch((err) => console.error("error loading data:", err));
  }, []);

  // just opens drawer + fills coords (no marker)
  function MapClickHandler() {
    useMapEvents({
      click(e) {
        const { lat, lng } = e.latlng;
        setClickedCoords({ lat, lng });
      },
    });
    return null;
  }

  return (
    <div className="h-screen w-full relative bg-[#FFF9F3]">
      <MapContainer
        center={[40.7128, -74.006]}
        zoom={11}
        scrollWheelZoom
        ref={mapRef}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
        />

        {reports.map((r) => (
          <CircleMarker
            key={r.UniqueKey}
            center={[r.Latitude, r.Longitude]}
            radius={4.5}
            pathOptions={{
              color:
                r.Status === "Closed"
                  ? "#9bf6ff"
                  : r.Status === "Open"
                  ? "#ffadad"
                  : "#ffd6a5",
              fillOpacity: 0.9,
            }}
          >
            <Popup>
              <div className="text-sm font-medium">
                <b>{r.Descriptor}</b>
                <br />
                Status: {r.Status}
                <br />
                Borough: {r.Borough}
                <br />
                Created: {r.CreatedDate}
              </div>
            </Popup>
          </CircleMarker>
        ))}

        <MapClickHandler />
      </MapContainer>

      {/* header */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/70 backdrop-blur-md px-5 py-2 rounded-full text-sm font-semibold shadow">
        🗽 NYC Plothole Map — {reports.length} reports
      </div>

      {/* drawer */}
      <ReportDrawer
        clickedCoords={clickedCoords}
        onDropMarker={(lat, lng) => {
          // no marker or popup — just center
          const map = mapRef.current;
          if (map) map.flyTo([lat, lng], 14);
        }}
      />
    </div>
  );
}
