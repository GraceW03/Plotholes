"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { useEffect, useState, useRef } from "react";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import L from "leaflet";
import { renderToString } from "react-dom/server";
import { MapPin } from "lucide-react";
import HeatmapControls, { HeatmapMode } from "./HeatmapControls";
import { fetchIssues, fetchNeighborhoodBoundaries, Issue, NeighborhoodFeature } from "../services/api";

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
  const neighborhoodLayerRef = useRef<L.LayerGroup | null>(null);

  const [heatmapMode, setHeatmapMode] = useState<HeatmapMode>('off');
  const [isLoading, setIsLoading] = useState(false);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [neighborhoods, setNeighborhoods] = useState<NeighborhoodFeature[]>([]);

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
        if (issues.length === 0) {
          loadIssues();
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
    if (heatmapMode === 'individual' && issues.length > 0) {
      createIssuesHeatmap();
    }
  }, [issues]);

  useEffect(() => {
    if (heatmapMode === 'neighborhoods' && neighborhoods.length > 0) {
      createNeighborhoodsLayer();
    }
  }, [neighborhoods]);

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