"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, X, Navigation, Target } from "lucide-react";

type Coords = { lat: number; lng: number } | null;

interface PathFinderDrawerProps {
  onRequestSelectOrigin?: () => void;
  onRequestSelectDestination?: () => void;
  onPathCalculated?: (origin: [number, number], destination: [number, number]) => void;
  clickedCoords?: { lat: number; lng: number } | null;
  selectMode?: "none" | "origin" | "destination"; // comes from NYCMap
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export default function PathFinderDrawer({
  onRequestSelectOrigin,
  onRequestSelectDestination,
  onPathCalculated,
  clickedCoords,
  selectMode = "none",
  isOpen: externalOpen,
  onOpenChange,
}: PathFinderDrawerProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = externalOpen ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;

  const [origin, setOrigin] = useState<Coords>(null);
  const [destination, setDestination] = useState<Coords>(null);
  const [originAddress, setOriginAddress] = useState("");
  const [destinationAddress, setDestinationAddress] = useState("");
  const [loading, setLoading] = useState(false);

  // reverse geocode for label
  const fetchAddress = async (lat: number, lng: number) => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`
      );
      const data = await res.json();
      return data?.display_name || "";
    } catch {
      return "";
    }
  };

useEffect(() => {
  if (!clickedCoords || selectMode === "none") return;
  const { lat, lng } = clickedCoords;
  (async () => {
    const addr = await fetchAddress(lat, lng);
    if (selectMode === "origin") { setOrigin({ lat, lng }); setOriginAddress(addr); }
    else if (selectMode === "destination") { setDestination({ lat, lng }); setDestinationAddress(addr); }
    setOpen(true);
  })();
}, [clickedCoords, selectMode]); // ← include selectMode


  const handleCalculatePath = () => {
    if (!origin || !destination) return alert("Please set both origin and destination!");
    setLoading(true);
    onPathCalculated?.([origin.lat, origin.lng], [destination.lat, destination.lng]);
    setTimeout(() => {
      setLoading(false);
      setOpen(false);
    }, 500);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="pathfinder"
          initial={{ x: -350 }}
          animate={{ x: 0 }}
          exit={{ x: -350 }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
          className="fixed top-0 left-0 h-full w-[340px] z-[1000] bg-white/95 backdrop-blur-xl shadow-2xl rounded-r-3xl border-r border-gray-200 flex flex-col"
        >
          {/* header */}
          <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <Navigation className="w-5 h-5 text-indigo-500" />
              Find a Path
            </h2>
            <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          </div>

          {/* body */}
          <div className="flex flex-col flex-grow gap-6 px-6 py-5 overflow-y-auto">
            {/* origin */}
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-sm flex items-center gap-2 text-gray-700">
                <MapPin className="w-4 h-4 text-green-500" /> Origin
              </label>
              {origin && (
                <p className="text-xs text-gray-500 bg-green-50 border border-green-200 rounded-md p-2">
                  📍 {origin.lat.toFixed(5)}, {origin.lng.toFixed(5)}
                </p>
              )}
              <div className="flex gap-2">
                <input
                  type="number"
                  step="any"
                  placeholder="Latitude"
                  value={origin?.lat ?? ""}
                  onChange={(e) =>
                    setOrigin((prev) => ({ lat: parseFloat(e.target.value), lng: prev?.lng ?? 0 }))
                  }
                  className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm"
                />
                <input
                  type="number"
                  step="any"
                  placeholder="Longitude"
                  value={origin?.lng ?? ""}
                  onChange={(e) =>
                    setOrigin((prev) => ({ lat: prev?.lat ?? 0, lng: parseFloat(e.target.value) }))
                  }
                  className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm"
                />
              </div>
              <button
                type="button"
                onClick={onRequestSelectOrigin}
                className="text-xs text-green-600 underline self-start mt-1"
              >
                🗺️ Select origin on map
              </button>
            </div>

            <div className="border-t border-gray-200" />

            {/* destination */}
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-sm flex items-center gap-2 text-gray-700">
                <Target className="w-4 h-4 text-red-500" /> Destination
              </label>
              {destination && (
                <p className="text-xs text-gray-500 bg-red-50 border border-red-200 rounded-md p-2">
                  🎯 {destination.lat.toFixed(5)}, {destination.lng.toFixed(5)}
                </p>
              )}
              <div className="flex gap-2">
                <input
                  type="number"
                  step="any"
                  placeholder="Latitude"
                  value={destination?.lat ?? ""}
                  onChange={(e) =>
                    setDestination((prev) => ({
                      lat: parseFloat(e.target.value),
                      lng: prev?.lng ?? 0,
                    }))
                  }
                  className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm"
                />
                <input
                  type="number"
                  step="any"
                  placeholder="Longitude"
                  value={destination?.lng ?? ""}
                  onChange={(e) =>
                    setDestination((prev) => ({
                      lat: prev?.lat ?? 0,
                      lng: parseFloat(e.target.value),
                    }))
                  }
                  className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm"
                />
              </div>
              <button
                type="button"
                onClick={onRequestSelectDestination}
                className="text-xs text-red-600 underline self-start mt-1"
              >
                🗺️ Select destination on map
              </button>
            </div>

            {/* button */}
            <motion.button
              type="button"
              whileTap={{ scale: 0.97 }}
              disabled={!origin || !destination || loading}
              onClick={handleCalculatePath}
              className="w-full mt-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded-md text-sm"
            >
              {loading ? "Calculating..." : "Calculate Path"}
            </motion.button>
          </div>

          {/* footer */}
          <div className="px-6 py-4 border-t border-gray-100 text-center text-xs text-gray-400">
            🧭 Powered by OSRM Routing
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
