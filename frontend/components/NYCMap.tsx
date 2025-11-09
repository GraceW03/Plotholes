"use client";

import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import L from "leaflet";
import { MapPin, Menu, X, FilePlus, Flame, Grid3x3, Navigation } from "lucide-react";
import { renderToString } from "react-dom/server";
import { HeatmapMode } from "./HeatmapControls";
import { fetchIssues, fetchNeighborhoodBoundaries, fetchReports, Issue, NeighborhoodFeature, Report as UserReport } from "../services/api";
import ReportDrawer from "@/components/ReportDrawer";
import PathFinderDrawer from "@/components/PathFinderDrawer";

interface Report {
  id: string;
  lat: number;
  lng: number;
  severity: number;
  confidence: number;
  created_at: string;
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
  const isPathSelection = useRef(false);

  useEffect(() => {
    // Check if we're in path selection mode
    isPathSelection.current = selecting && onSelectingChange === undefined;
    
    selectingRef.current = selecting;
    const el = map.getContainer();
    el.style.cursor = selecting ? "crosshair" : "";
    return () => {
      el.style.cursor = "";
    };
  }, [map, selecting, onSelectingChange]);

  useEffect(() => {
    const handleClick = (e: L.LeafletMouseEvent) => {
      if (!selectingRef.current) return;
      const { lat, lng } = e.latlng;
      onPick(lat, lng);
      // Only call onSelectingChange if we're not in path selection mode
      if (!isPathSelection.current) {
        onSelectingChange?.(false);
      }
    };

    map.on("click", handleClick);
    return () => {
      map.off("click", handleClick);
    };
  }, [map, onPick, onSelectingChange]);

  return null;
}

function subtlePlural(count: number) {
  return count === 1 ? " report" : " reports";
}

// Component to automatically fit map to route (but only once per route)
function FitBounds({ route }: { route: [number, number][] }) {
  const map = useMap();
  const hasFittedRef = useRef(false);
  const prevHashRef = useRef<string>("");

  useEffect(() => {
    if (route.length === 0) return;

    const hash = route.map(([lat, lng]) => `${lat.toFixed(3)},${lng.toFixed(3)}`).join("|");

    if (hash !== prevHashRef.current) {
      prevHashRef.current = hash;
      hasFittedRef.current = false;
    }

    if (!hasFittedRef.current) {
      const bounds = L.latLngBounds(route);
      map.fitBounds(bounds, { padding: [50, 50] });
      hasFittedRef.current = true;
    }
  }, [route, map]);

  return null;
}

export default function NYCMap() {
  const [reports, setReports] = useState<UserReport[]>([]);
  const [clickedCoords, setClickedCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [selecting, setSelecting] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [pathFinderOpen, setPathFinderOpen] = useState(false);
  const [selectingForPath, setSelectingForPath] = useState<'none' | 'origin' | 'destination'>('none');
  const [pathOrigin, setPathOrigin] = useState<{ lat: number; lng: number } | null>(null);
  const [pathDestination, setPathDestination] = useState<{ lat: number; lng: number } | null>(null);
  const [reportCoords, setReportCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [pathClickCoords, setPathClickCoords] = useState<{ lat: number; lng: number } | null>(null);

  const mapRef = useRef<L.Map | null>(null);

  /** Lucide pin icon rendered as static HTML for Leaflet */
  const lucidePinIcon = L.divIcon({
    html: `<div style="transform: translate(-50%, -100%); display:flex;align-items:center;justify-content:center;">${renderToString(<MapPin size={26} color="#FF6B6B" />)}</div>`,
    className: "",
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  });

  const lucideMarkerIcon = L.divIcon({
    html: renderToString(<MapPin size={24} color="#3B82F6" />),
    className: "",
    iconSize: [24, 24],
    iconAnchor: [12, 24]
  });

/** Called when user clicks the map */
const handlePick = (lat: number, lng: number) => {
  if (selectingForPath !== "none") {
    if (selectingForPath === "origin") setPathOrigin({ lat, lng });
    else setPathDestination({ lat, lng });

    setPathClickCoords({ lat, lng });   // ← only for PathFinder
    setPathFinderOpen(true);
    setTimeout(() => setSelectingForPath("none"), 0); // no report side-effects
  } else if (selecting) {
    setReportCoords({ lat, lng });      // ← only for Report
    setSelecting(false);
    setDrawerOpen(true);
  }
  mapRef.current?.flyTo([lat, lng], 15);
};


  /** Called from drawer when "Select on map" clicked */
  const handleRequestSelect = () => {
    setSelecting(true);
    setClickedCoords(null);
  };

  /** Called from nav menu when "New Report" clicked */
  const handleOpenNewReport = () => {
    setDrawerOpen(true);
  };

  /** Called from nav menu when "Find a Path" clicked */
  const handleOpenPathFinder = () => {
    setPathFinderOpen(true);
  };

  /** Called when PathFinder calculates a new route */
  const handlePathCalculated = async (origin: [number, number], destination: [number, number]) => {
    const newRoute = await fetchOSRMRoute(origin, destination);
    setRoute(newRoute);
  };

  /** Called when drawer geocodes or uses my location */
  const handleDropMarker = (lat: number, lng: number) => {
    setClickedCoords({ lat, lng });
    mapRef.current?.flyTo([lat, lng], 15);
  };

  const center: [number, number] = [40.7128, -74.0060];
  const [route, setRoute] = useState<[number, number][]>([]);
  const [showNav, setShowNav] = useState(false);

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
      return [start, end];
    }
  };

  useEffect(() => {
    // Don't auto-load route on mount - user will trigger it via PathFinder
  }, []);

  const heatLayerRef = useRef<any>(null);
  const neighborhoodLayerRef = useRef<L.LayerGroup | null>(null);

  const [heatmapMode, setHeatmapMode] = useState<HeatmapMode>('individual');
  const [showHeatmapPanel, setShowHeatmapPanel] = useState(false);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [neighborhoods, setNeighborhoods] = useState<NeighborhoodFeature[]>([]);
  const [userReports, setUserReports] = useState<UserReport[]>([]);

  const handleMapReady = (map: L.Map) => {
    mapRef.current = map;
  };

  const [issuesLoading, setIssuesLoading] = useState(false);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [neighborhoodsLoading, setNeighborhoodsLoading] = useState(false);

  const loadIssues = async () => {
    if (issuesLoading) return;
    try {
      setIssuesLoading(true);
      const data = await fetchIssues();
      setIssues(data.issues);
    } catch (error) {
      console.error('Failed to load issues:', error);
    } finally {
      setIssuesLoading(false);
    }
  };

  const loadReports = async () => {
    if (reportsLoading) return;
    try {
      setReportsLoading(true);
      const data = await fetchReports();
      setUserReports(data.reports);
      setReports(data.reports); // ✅ new line — update main reports array too
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setReportsLoading(false);
    }
  };


  const loadNeighborhoods = async () => {
    if (neighborhoodsLoading) return;
    try {
      setNeighborhoodsLoading(true);
      const data = await fetchNeighborhoodBoundaries();
      setNeighborhoods(data.features);
    } catch (error) {
      console.error('Failed to load neighborhoods:', error);
    } finally {
      setNeighborhoodsLoading(false);
    }
  };

  const createIssuesHeatmap = () => {
    if (!mapRef.current || (issues.length === 0 && userReports.length === 0)) return;

    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
    }

    const issuePoints: [number, number, number][] = issues
      .filter(issue => issue.latitude && issue.longitude)
      .map(issue => [issue.latitude, issue.longitude, issue.severity / 5]);

    const reportPoints: [number, number, number][] = userReports
      .filter(report => report.latitude && report.longitude)
      .map(report => [report.latitude, report.longitude, Math.max(report.severity / 3, 0.6)]);

    const allHeatPoints = [...issuePoints, ...reportPoints];

    if (allHeatPoints.length === 0) return;

    heatLayerRef.current = (L as any).heatLayer(allHeatPoints, {
      radius: 25,
      blur: 15,
      maxZoom: 17,
      gradient: {
        0.2: '#00ff00',
        0.4: '#ffff00',
        0.6: '#ff9900',
        0.8: '#ff0000',
        1.0: '#990000'
      }
    });

    mapRef.current.addLayer(heatLayerRef.current);
  };

  const createNeighborhoodsLayer = () => {
    if (!mapRef.current || neighborhoods.length === 0) return;

    if (neighborhoodLayerRef.current) {
      mapRef.current.removeLayer(neighborhoodLayerRef.current);
    }

    neighborhoodLayerRef.current = L.layerGroup();

    neighborhoods.forEach(feature => {
      const coordinates = feature.geometry.coordinates[0].map(coord => [coord[1], coord[0]] as [number, number]);

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

  useEffect(() => {
    if (!mapRef.current) return;

    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }
    if (neighborhoodLayerRef.current) {
      mapRef.current.removeLayer(neighborhoodLayerRef.current);
      neighborhoodLayerRef.current = null;
    }

    switch (heatmapMode) {
      case 'individual':
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
    }
  }, [heatmapMode, mapRef.current]);

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

  useEffect(() => {
    loadReports();
  }, []);

  // TODO: ADD FRONTEND FOR THIS --- THIS IS UNTESTED!!
  const callCortex = async (prompt: string) => {
    try {
      const response = await fetch("/api/run_cortex", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Cortex API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log("Cortex results:", data.results);
      return data.results; // This will be your SQL query results array
    } catch (err) {
      console.error("Error calling Cortex API:", err);
      return null;
    }
  };

const [showSplash, setShowSplash] = useState(true);
const [fadeOut, setFadeOut] = useState(false);

useEffect(() => {
  // Step 1: show splash for ~2 seconds
  const timer = setTimeout(() => {
    setFadeOut(true); // trigger fade-out CSS
    // Step 2: unmount after fade transition
    setTimeout(() => setShowSplash(false), 800);
  }, 2000);

  return () => clearTimeout(timer);
}, []);



  return (
    <div className="h-screen w-full relative bg-[#FFF9F3]">
      {/* Fancy NYC Loading Screen */}
      {showSplash && (
      <div
        className={`absolute inset-0 z-[2000] flex flex-col items-center justify-center
          bg-gradient-to-b from-[#FFF9F3] to-[#FFEEDA] backdrop-blur-md
          transition-opacity duration-700 ease-out ${
            fadeOut ? "opacity-0" : "opacity-100"
          }`}
      >
        <div className="flex flex-col items-center animate-fadeIn">
          <div className="text-6xl mb-3 animate-bounce">🚧</div>
          <h1 className="text-2xl font-extrabold text-[#FF6B6B] tracking-tight">
            Loading Plothole NYC
          </h1>
          <p className="text-sm text-gray-500 mt-1 mb-6">
            Detecting potholes and rendering streets...
          </p>

          <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden shadow-inner">
            <div className="h-full bg-[#FF6B6B] animate-[progress_2s_ease-in-out_infinite]" />
          </div>
        </div>

        <style jsx>{`
          @keyframes progress {
            0% {
              transform: translateX(-100%);
            }
            50% {
              transform: translateX(0%);
            }
            100% {
              transform: translateX(100%);
            }
          }
          .animate-fadeIn {
            animation: fadeIn 1.2s ease-out;
          }
          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}</style>
      </div>
    )}


      <MapContainer
        center={center}
        zoom={11}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <MapRefBridge onInit={handleMapReady} />

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

        {/* Route Polyline & Pins */}
        {route.length > 0 && (
          <Polyline positions={route} color="#FF6B6B" weight={4} />
        )}

        {/* Temporary route selection pins */}
        {pathOrigin && (
          <Marker position={[pathOrigin.lat, pathOrigin.lng]} icon={lucideMarkerIcon}>
            <Popup>📍 Origin</Popup>
          </Marker>
        )}
        {pathDestination && (
          <Marker position={[pathDestination.lat, pathDestination.lng]} icon={lucideMarkerIcon}>
            <Popup>🎯 Destination</Popup>
          </Marker>
        )}

        {/* Report pin */}
        {reportCoords && (
          <Marker position={[reportCoords.lat, reportCoords.lng]} icon={lucidePinIcon}>
            <Popup>
              <div className="text-sm">
                📍 Selected Location
                <br />
                ({reportCoords.lat.toFixed(4)}, {reportCoords.lng.toFixed(4)})
              </div>
            </Popup>
          </Marker>
        )}

        {/* Fit map to route */}
        <FitBounds route={route} />

        {/* Render existing pothole reports */}
        {reports.map((r) => (
          <CircleMarker
            key={`${r.id}-${r.latitude}-${r.longitude}`}
            center={[r.latitude, r.longitude]}
            radius={4.5}
            pathOptions={{
              color: "#FF6B6B",
              fillOpacity: 0.9,
            }}
          >
            <Popup>
              <div className="text-sm font-medium leading-tight">
                <b>Reported Pothole</b><br />
                Severity: {r.severity}<br />
                Confidence: {(r.confidence * 100).toFixed(1)}%<br />
                Created: {new Date(r.created_at).toLocaleString()}
              </div>

              {/* 🖼️ Image Preview (if available) */}
              {r.image_url && (
                <div className="mt-2">
                  <img
                    src={r.image_url}
                    alt="Pothole report"
                    className="w-48 h-32 object-cover rounded-md border border-gray-300 shadow-sm"
                  />
                </div>
              )}
            </Popup>
          </CircleMarker>
        ))}


        {/* Pin for selected location */}
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

        <ClickHandler
          selecting={selecting || selectingForPath !== "none"}
          onPick={handlePick}
          onSelectingChange={selectingForPath === "none" ? setSelecting : undefined}
        />
      </MapContainer>
      
      {/* Header */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/80 backdrop-blur-md px-6 py-2 rounded-full text-sm font-semibold text-[#2B2B2B] shadow-md border border-[#f0f0f0]">
        🗽 NYC Pothole Reports • <span className="font-bold text-[#FF6B6B]">{reports.length}</span> 
        {subtlePlural(reports.length)}
      </div>

      {/* Unified Navigation Menu */}
      <div className="fixed top-4 right-4 z-[1001]">
        <button
          onClick={() => setShowNav(!showNav)}
          className="p-3 rounded-full bg-white/90 shadow-lg hover:bg-white transition-all border border-gray-200"
          aria-label="Navigation menu"
        >
          {showNav ? <X className="w-5 h-5 text-gray-800" /> : <Menu className="w-5 h-5 text-gray-800" />}
        </button>

        {showNav && (
          <div className="absolute right-0 mt-3 w-56 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
            <button
              onClick={() => {
                setShowHeatmapPanel(!showHeatmapPanel);
                setShowNav(false);
              }}
              className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-800 hover:bg-gray-50 transition-colors border-b border-gray-100"
            >
              <Flame className="w-4 h-4 mr-3 text-orange-500" />
              Heatmap Options
            </button>

            <button
              onClick={() => {
                handleOpenPathFinder();
                setShowNav(false);
              }}
              className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-800 hover:bg-gray-50 transition-colors border-b border-gray-100"
            >
              <Navigation className="w-4 h-4 mr-3 text-indigo-500" />
              Find a Path
            </button>

            <button
              onClick={() => {
                handleOpenNewReport();
                setShowNav(false);
              }}
              className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-800 hover:bg-gray-50 transition-colors"
            >
              <FilePlus className="w-4 h-4 mr-3 text-green-500" />
              New Report
            </button>
          </div>
        )}
      </div>

      {/* Heatmap Control Panel */}
      {showHeatmapPanel && (
        <div className="fixed top-20 right-4 z-[1000] w-72 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-bold text-gray-800 flex items-center gap-2">
              <Flame className="w-5 h-5 text-orange-500" />
              Heatmap Options
            </h3>
            <button
              onClick={() => setShowHeatmapPanel(false)}
              className="text-gray-400 hover:text-gray-600 transition"
            >
              <X size={18} />
            </button>
          </div>

          <div className="p-4 space-y-3">
            <button
              onClick={() => setHeatmapMode(prev => prev === 'individual' ? 'off' : 'individual')}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                heatmapMode === 'individual' 
                  ? 'bg-orange-50 border-2 border-orange-400 text-orange-700' 
                  : 'bg-gray-50 border-2 border-transparent hover:border-gray-300 text-gray-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <Flame className={`w-5 h-5 ${heatmapMode === 'individual' ? 'text-orange-500' : 'text-gray-400'}`} />
                <span className="font-medium text-sm">Individual Issues</span>
              </div>
              {heatmapMode === 'individual' && (
                <div className="w-2 h-2 rounded-full bg-orange-500"></div>
              )}
            </button>

            <button
              onClick={() => setHeatmapMode(prev => prev === 'neighborhoods' ? 'off' : 'neighborhoods')}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                heatmapMode === 'neighborhoods' 
                  ? 'bg-purple-50 border-2 border-purple-400 text-purple-700' 
                  : 'bg-gray-50 border-2 border-transparent hover:border-gray-300 text-gray-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <Grid3x3 className={`w-5 h-5 ${heatmapMode === 'neighborhoods' ? 'text-purple-500' : 'text-gray-400'}`} />
                <span className="font-medium text-sm">Neighborhood Risk</span>
              </div>
              {heatmapMode === 'neighborhoods' && (
                <div className="w-2 h-2 rounded-full bg-purple-500"></div>
              )}
            </button>

            {heatmapMode !== 'off' && (
              <button
                onClick={() => setHeatmapMode('off')}
                className="w-full px-4 py-2 text-xs font-medium text-gray-500 hover:text-gray-700 transition"
              >
                Clear Heatmap
              </button>
            )}
          </div>

          {(issuesLoading || reportsLoading || neighborhoodsLoading) && (
            <div className="px-4 pb-4 flex items-center justify-center gap-2 text-xs text-gray-500">
              <div className="w-3 h-3 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
              Loading data...
            </div>
          )}
        </div>
      )}

      {/* Click-outside backdrop for heatmap panel */}
      {showHeatmapPanel && (
        <div
          className="fixed inset-0 z-[999]"
          onClick={() => setShowHeatmapPanel(false)}
        />
      )}

      {/* Selection banner */}
      {(selecting || selectingForPath !== 'none') && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000] bg-[#FFD6A5] text-[#2B2B2B] px-5 py-2.5 rounded-full text-sm font-semibold shadow-lg border border-[#f0e3c0]">
          👆 Click anywhere on the map to choose {selectingForPath !== 'none' ? selectingForPath : 'a location'}
        </div>
      )}

      {/* PathFinder Drawer */}
      <PathFinderDrawer
        isOpen={pathFinderOpen}
        onOpenChange={setPathFinderOpen}
        clickedCoords={pathClickCoords}          // ← not report coords
        selectMode={selectingForPath}
        onRequestSelectOrigin={() => { setSelectingForPath("origin"); setPathClickCoords(null); }}
        onRequestSelectDestination={() => { setSelectingForPath("destination"); setPathClickCoords(null); }}
        onPathCalculated={handlePathCalculated}
      />

      <ReportDrawer
        clickedCoords={reportCoords}             // ← report-only coords
        onDropMarker={(lat, lng) => {
          setReportCoords({ lat, lng });
          mapRef.current?.flyTo([lat, lng], 15);
        }}
        onRequestSelect={() => {
          setSelecting(true);
          setReportCoords(null);
        }}
        isOpen={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </div>
  );
}