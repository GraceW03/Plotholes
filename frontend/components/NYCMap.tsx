"use client";

import React, { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import L from "leaflet";
import { MapPin } from "lucide-react";
import { renderToString } from "react-dom/server";
import HeatmapControls, { HeatmapMode } from "./HeatmapControls";
import { fetchIssues, fetchNeighborhoodBoundaries, fetchReports, Issue, NeighborhoodFeature, Report as UserReport } from "../services/api";
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
  const [reports] = useState<Report[]>([]); // Empty array since we load from API
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
  const heatLayerRef = useRef<any>(null); // Using any for leaflet.heat layer
  const neighborhoodLayerRef = useRef<L.LayerGroup | null>(null);

  const [heatmapMode, setHeatmapMode] = useState<HeatmapMode>('off');
  const [isLoading, setIsLoading] = useState(false);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [neighborhoods, setNeighborhoods] = useState<NeighborhoodFeature[]>([]);
  const [userReports, setUserReports] = useState<UserReport[]>([]);

  // Initialize map ref
  const handleMapReady = (map: L.Map) => {
    mapRef.current = map;
  };

  // Load individual issues data
  const loadIssues = async () => {
    try {
      setIsLoading(true);
      const data = await fetchIssues();
      setIssues(data.issues);
    } catch (error) {
      console.error('Failed to load issues:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load user reports data
  const loadReports = async () => {
    try {
      setIsLoading(true);
      const data = await fetchReports();
      setUserReports(data.reports);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load neighborhood boundaries data
  const loadNeighborhoods = async () => {
    try {
      setIsLoading(true);
      const data = await fetchNeighborhoodBoundaries();
      setNeighborhoods(data.features);
    } catch (error) {
      console.error('Failed to load neighborhoods:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Create heatmap layer from issues and user reports
  const createIssuesHeatmap = () => {
    if (!mapRef.current || (issues.length === 0 && userReports.length === 0)) return;

    // Remove existing heat layer
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
    }

    // Convert issues to heatmap points [lat, lng, intensity]
    const issuePoints: [number, number, number][] = issues
      .filter(issue => issue.latitude && issue.longitude)
      .map(issue => [
        issue.latitude,
        issue.longitude,
        issue.severity / 5 // Normalize severity (1-5) to (0.2-1.0)
      ]);

    // Convert user reports to heatmap points [lat, lng, intensity]
    const reportPoints: [number, number, number][] = userReports
      .filter(report => report.latitude && report.longitude)
      .map(report => [
        report.latitude,
        report.longitude,
        Math.max(report.severity / 5, 0.4) // Normalize severity (1-5) to (0.2-1.0), with minimum 0.4 for visibility
      ]);

    // Combine all points
    const allHeatPoints = [...issuePoints, ...reportPoints];

    if (allHeatPoints.length === 0) return;

    // Create heat layer with severity-based gradient
    heatLayerRef.current = (L as any).heatLayer(allHeatPoints, {
      radius: 25,
      blur: 15,
      maxZoom: 17,
      gradient: {
        0.2: '#00ff00', // Low severity - green
        0.4: '#ffff00', // Low-medium severity - yellow
        0.6: '#ff9900', // Medium severity - orange
        0.8: '#ff0000', // High severity - red
        1.0: '#990000'  // Critical severity - dark red
      }
    });

    mapRef.current.addLayer(heatLayerRef.current);
  };

  // Create neighborhood polygons layer
  const createNeighborhoodsLayer = () => {
    if (!mapRef.current || neighborhoods.length === 0) return;

    // Remove existing neighborhood layer
    if (neighborhoodLayerRef.current) {
      mapRef.current.removeLayer(neighborhoodLayerRef.current);
    }

    neighborhoodLayerRef.current = L.layerGroup();

    neighborhoods.forEach(feature => {
      // Create polygon from GeoJSON geometry
      const coordinates = feature.geometry.coordinates[0].map(coord => [coord[1], coord[0]] as [number, number]);

      // Color based on risk level
      const getNeighborhoodStyle = (riskLevel: string) => {
        switch (riskLevel) {
          case 'critical': return { color: '#990000', fillColor: '#990000', fillOpacity: 0.6 };
          case 'high': return { color: '#ff0000', fillColor: '#ff0000', fillOpacity: 0.5 };
          case 'medium': return { color: '#ff9900', fillColor: '#ff9900', fillOpacity: 0.4 };
          case 'low': return { color: '#ffff00', fillColor: '#ffff00', fillOpacity: 0.3 };
          default: return { color: '#00ff00', fillColor: '#00ff00', fillOpacity: 0.2 };
        }
      };

      const polygon = L.polygon(coordinates, {
        ...getNeighborhoodStyle(feature.properties.risk_level),
        weight: 2
      });

      // Add popup with neighborhood information
      polygon.bindPopup(`
        <div class="p-2">
          <h3 class="font-semibold text-lg">${feature.properties.neighborhood || 'Unknown Neighborhood'}</h3>
          <div class="mt-2 space-y-1 text-sm">
            <div><strong>Borough:</strong> ${feature.properties.borough || 'Unknown'}</div>
            <div><strong>Risk Level:</strong> ${feature.properties.risk_level.toUpperCase()}</div>
            <div><strong>Issues:</strong> ${feature.properties.issue_count}</div>
            <div><strong>Avg Severity:</strong> ${feature.properties.avg_severity.toFixed(1)}/5</div>
            <div><strong>Risk Score:</strong> ${feature.properties.risk_score.toFixed(2)}</div>
          </div>
        </div>
      `);

      neighborhoodLayerRef.current!.addLayer(polygon);
    });

    mapRef.current.addLayer(neighborhoodLayerRef.current);
  };

  // Handle heatmap mode changes
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove existing layers
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }
    if (neighborhoodLayerRef.current) {
      mapRef.current.removeLayer(neighborhoodLayerRef.current);
      neighborhoodLayerRef.current = null;
    }

    // Add appropriate layer based on mode
    switch (heatmapMode) {
      case 'individual':
        // Load both issues and reports if not already loaded
        const needsIssues = issues.length === 0;
        const needsReports = userReports.length === 0;

        if (needsIssues && needsReports) {
          Promise.all([loadIssues(), loadReports()]);
        } else if (needsIssues) {
          loadIssues();
        } else if (needsReports) {
          loadReports();
        } else {
          createIssuesHeatmap();
        }
        break;
      case 'neighborhoods':
        if (neighborhoods.length === 0) {
          loadNeighborhoods();
        } else {
          createNeighborhoodsLayer();
        }
        break;
      case 'off':
      default:
        // Layers already removed above
        break;
    }
  }, [heatmapMode, mapRef.current]);

  // Create heatmap when data is loaded
  useEffect(() => {
    if (heatmapMode === 'individual' && (issues.length > 0 || userReports.length > 0)) {
      createIssuesHeatmap();
    }
  }, [issues, userReports]);

  useEffect(() => {
    if (heatmapMode === 'neighborhoods' && neighborhoods.length > 0) {
      createNeighborhoodsLayer();
    }
  }, [neighborhoods]);

  return (

    <div className="h-screen w-full relative bg-[#FFF9F3]">
      <MapContainer
        center={[40.7128, -74.006]}
        zoom={11}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      // whenCreated={handleMapReady}
      >
        {/* hand the real map instance to mapRef */}
        <MapRefBridge onInit={handleMapReady} />

        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
        />

        {/* Render existing pothole reports */}
        {reports.map((r) => (
          <CircleMarker
            key={r.UniqueKey}
            center={[r.Latitude, r.Longitude]}
            radius={4.5}
            pathOptions={{
              color:
                r.Status === "Closed" ? "#9bf6ff" :
                  r.Status === "Open" ? "#ffadad" :
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

        {/* 📍 Pin for selected or searched location */}
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

        {/* Map center marker */}
        <Marker position={center} icon={lucidePinIcon}>
          <Popup>
            <div className="font-semibold">📍 New York City</div>
            <p className="text-sm text-zinc-600">NYC map with custom marker</p>
          </Popup>
        </Marker>

        {/* Origin marker */}
        <Marker position={origin} icon={lucidePinIcon}>
          <Popup>Origin</Popup>
        </Marker>

        {/* Destination marker */}
        <Marker position={destination} icon={lucidePinIcon}>
          <Popup>Destination</Popup>
        </Marker>

        {/* Route Polyline */}
        {route.length > 0 && (
          <Polyline positions={route} color="red" weight={4} />
        )}

        {/* Fit map to route */}
        <FitBounds route={route} />

        <ClickHandler selecting={selecting} onPick={handlePick} onSelectingChange={setSelecting} />
      </MapContainer>

      {/* Header */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/80 backdrop-blur-md px-6 py-2 rounded-full text-sm sm:text-base font-semibold text-[#2B2B2B] shadow-md border border-[#f0f0f0]">
        🗽 NYC Pothole Reports •{" "}
        <span className="font-bold text-[#FF6B6B]">{reports.length}</span>{" "}
        {reports.length === 1 ? "report" : "reports"}
      </div>

      {/* Selection banner */}
      {selecting && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000] bg-[#FFD6A5] text-[#2B2B2B] px-4 py-2 rounded-full text-sm font-semibold shadow-md border border-[#f0e3c0]">
          👆 Click anywhere on the map to choose a location
        </div>
      )}

      {/* Heatmap Controls */}
      <HeatmapControls
        mode={heatmapMode}
        onModeChange={setHeatmapMode}
        isLoading={isLoading}
      />

      {/* Drawer */}
      <ReportDrawer
        clickedCoords={clickedCoords}
        onDropMarker={handleDropMarker}
        onRequestSelect={handleRequestSelect}
      />
    </div>
  );
}
