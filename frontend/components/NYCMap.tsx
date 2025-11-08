"use client";

import { MapContainer, TileLayer, Marker, Popup, Rectangle } from "react-leaflet";
import { useEffect, useState, useRef } from "react";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import L from "leaflet";
import { renderToString } from "react-dom/server";
import { MapPin } from "lucide-react";
import HeatmapControls, { HeatmapMode } from "./HeatmapControls";
import { fetchIssues, fetchGridZones, Issue, GridZone } from "../services/api";

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
  const mapRef = useRef<L.Map | null>(null);
  const heatLayerRef = useRef<any>(null); // Using any for leaflet.heat layer
  // const gridLayerRef = useRef<L.LayerGroup | null>(null);

  const [heatmapMode, setHeatmapMode] = useState<HeatmapMode>('off');
  const [isLoading, setIsLoading] = useState(false);
  const [issues, setIssues] = useState<Issue[]>([]);
  // const [gridZones, setGridZones] = useState<GridZone[]>([]);

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

  // Load grid zones data
  // const loadGridZones = async () => {
  //   try {
  //     setIsLoading(true);
  //     const data = await fetchGridZones();
  //     setGridZones(data.zones);
  //   } catch (error) {
  //     console.error('Failed to load grid zones:', error);
  //   } finally {
  //     setIsLoading(false);
  //   }
  // };

  // Create heatmap layer from issues
  const createIssuesHeatmap = () => {
    if (!mapRef.current || issues.length === 0) return;

    // Remove existing heat layer
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
    }

    // Convert issues to heatmap points [lat, lng, intensity]
    const heatPoints: [number, number, number][] = issues
      .filter(issue => issue.latitude && issue.longitude)
      .map(issue => [
        issue.latitude,
        issue.longitude,
        issue.severity / 5 // Normalize severity (1-5) to (0.2-1.0)
      ]);

    // Create heat layer with severity-based gradient
    heatLayerRef.current = (L as any).heatLayer(heatPoints, {
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

  // // Create grid zones layer
  // const createGridZonesLayer = () => {
  //   if (!mapRef.current || gridZones.length === 0) return;

  //   // Remove existing grid layer
  //   if (gridLayerRef.current) {
  //     mapRef.current.removeLayer(gridLayerRef.current);
  //   }

  //   gridLayerRef.current = L.layerGroup();

  //   gridZones.forEach(zone => {
  //     // Create rectangle for grid zone
  //     const bounds: L.LatLngBoundsExpression = [
  //       [zone.bounds.min_lat, zone.bounds.min_lng],
  //       [zone.bounds.max_lat, zone.bounds.max_lng]
  //     ];

  //     // Color based on risk level
  //     const getZoneStyle = (riskLevel: string) => {
  //       switch (riskLevel) {
  //         case 'critical': return { color: '#990000', fillColor: '#990000', fillOpacity: 0.6 };
  //         case 'high': return { color: '#ff0000', fillColor: '#ff0000', fillOpacity: 0.5 };
  //         case 'medium': return { color: '#ff9900', fillColor: '#ff9900', fillOpacity: 0.4 };
  //         case 'low': return { color: '#ffff00', fillColor: '#ffff00', fillOpacity: 0.3 };
  //         default: return { color: '#00ff00', fillColor: '#00ff00', fillOpacity: 0.2 };
  //       }
  //     };

  //     const rectangle = L.rectangle(bounds, {
  //       ...getZoneStyle(zone.risk_level),
  //       weight: 2
  //     });

  //     // Add popup with zone information
  //     rectangle.bindPopup(`
  //       <div class="p-2">
  //         <h3 class="font-semibold text-lg">${zone.risk_level.toUpperCase()} Risk Zone</h3>
  //         <div class="mt-2 space-y-1 text-sm">
  //           <div><strong>Issues:</strong> ${zone.issue_count}</div>
  //           <div><strong>Avg Severity:</strong> ${zone.avg_severity}/5</div>
  //           <div><strong>Risk Score:</strong> ${zone.risk_score}</div>
  //           <div><strong>Accessibility:</strong> ${zone.accessibility_score}/10</div>
  //           ${zone.boroughs.length > 0 ? `<div><strong>Boroughs:</strong> ${zone.boroughs.join(', ')}</div>` : ''}
  //         </div>
  //       </div>
  //     `);

  //     gridLayerRef.current!.addLayer(rectangle);
  //   });

  //   mapRef.current.addLayer(gridLayerRef.current);
  // };

  // Handle heatmap mode changes
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove existing layers
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }
    // if (gridLayerRef.current) {
    //   mapRef.current.removeLayer(gridLayerRef.current);
    //   gridLayerRef.current = null;
    // }

    // Add appropriate layer based on mode
    switch (heatmapMode) {
      case 'individual':
        if (issues.length === 0) {
          loadIssues();
        } else {
          createIssuesHeatmap();
        }
        break;
      // case 'grid':
      //   if (gridZones.length === 0) {
      //     loadGridZones();
      //   } else {
      //     createGridZonesLayer();
      //   }
      //   break;
      case 'off':
      default:
        // Layers already removed above
        break;
    }
  }, [heatmapMode, mapRef.current]);

  // Create heatmap when data is loaded
  useEffect(() => {
    if (heatmapMode === 'individual' && issues.length > 0) {
      createIssuesHeatmap();
    }
  }, [issues]);

  // useEffect(() => {
  //   if (heatmapMode === 'grid' && gridZones.length > 0) {
  //     createGridZonesLayer();
  //   }
  // }, [gridZones]);

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom
        ref={handleMapReady}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        <Marker position={center} icon={lucideMarkerIcon}>
          <Popup>
            <div className="font-semibold">📍 New York City</div>
            <p className="text-sm text-zinc-600">NYC map with heatmap functionality</p>
          </Popup>
        </Marker>
      </MapContainer>

      <HeatmapControls
        mode={heatmapMode}
        onModeChange={setHeatmapMode}
        isLoading={isLoading}
      />
    </div>
  );
}