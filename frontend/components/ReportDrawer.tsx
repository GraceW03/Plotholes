"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, MapPin, X } from "lucide-react";
import confetti from "canvas-confetti";

type Coords = { lat: number; lng: number } | null;

interface ReportDrawerProps {
  onDropMarker?: (lat: number, lng: number) => void;
  clickedCoords?: { lat: number; lng: number } | null;
  onRequestSelect: () => void;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export default function ReportDrawer({
  onDropMarker,
  clickedCoords,
  onRequestSelect,
  isOpen: externalOpen,
  onOpenChange,
}: ReportDrawerProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = externalOpen !== undefined ? externalOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;
  const [file, setFile] = useState<File | null>(null);
  const [coords, setCoords] = useState<Coords>(null);
  const [address, setAddress] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [dragOver, setDragOver] = useState(false);

  // ✅ simplified - just call it directly
  const handleRequestSelect = () => {
    console.log("🗺️ Select on map clicked");
    onRequestSelect(); // call parent's handler
    setOpen(false); // close drawer so user can see map
  };

  // 🌎 reverse-geocode coords → readable address
  const fetchAddress = async (lat: number, lng: number) => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`
      );
      const data = await res.json();
      if (data?.display_name) setAddress(data.display_name);
    } catch (e) {
      console.error("reverse-geocode error:", e);
    }
  };

  // 🧭 when user clicks map, prefill coords + open drawer + fetch address
  useEffect(() => {
    if (clickedCoords) {
      setCoords(clickedCoords);
      fetchAddress(clickedCoords.lat, clickedCoords.lng);
      setOpen(true);
    }
  }, [clickedCoords]);

  // 📍 Use my location
  const handleUseMyLocation = () => {
    if (!navigator.geolocation) return alert("Geolocation not supported!");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const newCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setCoords(newCoords);
        onDropMarker?.(newCoords.lat, newCoords.lng);
        fetchAddress(newCoords.lat, newCoords.lng);
      },
      () => alert("Permission denied.")
    );
  };

  // 🖱️ Drag-and-drop upload
  const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  };

  // 🚀 Submit
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) return alert("Please upload an image first!");
    if (!coords?.lat || !coords?.lng)
      return alert("Please enter or choose a location before submitting!");

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("lat", String(coords.lat));
    formData.append("lng", String(coords.lng));

    try {
      const res = await fetch("/api/report", { method: "POST", body: formData });
      const data = await res.json();
      setResult(data);

      if (!data.error) {
        confetti({
          particleCount: 120,
          spread: 70,
          origin: { y: 0.7 },
          colors: ["#FFADAD", "#FFD6A5", "#B9FBC0", "#CDB4DB"],
        });
        onDropMarker?.(coords.lat, coords.lng);
      } else {
        alert("Server error: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      console.error(err);
      alert("Upload failed — check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Drawer */}
      <AnimatePresence>
        {open && (
          <motion.div
            key="drawer"
            initial={{ x: -350 }}
            animate={{ x: 0 }}
            exit={{ x: -350 }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
            className="fixed top-0 left-0 h-full w-[330px] z-[1000] bg-white/95 backdrop-blur-xl shadow-2xl rounded-r-3xl border-r border-[#f2f2f2] flex flex-col justify-between"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-[#f5f5f5]">
              <h2 className="text-lg font-extrabold text-[#2B2B2B] flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#FF6B6B]" /> New Report
              </h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition"
              >
                <X size={18} />
              </button>
            </div>

            {/* Form */}
            <form
              onSubmit={handleSubmit}
              className="flex flex-col flex-grow justify-start gap-6 px-6 py-5 overflow-y-auto"
            >
              {/* Upload */}
              <div className="flex flex-col gap-2">
                <label className="font-semibold text-sm text-gray-700">
                  Upload a road photo:
                </label>
                <label
                  htmlFor="file-upload"
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl py-8 text-[#555] transition cursor-pointer ${
                    dragOver
                      ? "border-[#FFADAD] bg-[#FFF0F0]"
                      : "border-[#FFD6A5] hover:bg-[#FFF9F3]"
                  }`}
                >
                  <Upload className="w-6 h-6 text-[#FFADAD]" />
                  <span className="text-xs font-medium">
                    {file ? file.name : "Click or drag an image here"}
                  </span>
                </label>
                <input
                  id="file-upload"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                {file && (
                  <img
                    src={URL.createObjectURL(file)}
                    alt="Preview"
                    className="mt-2 w-full h-32 object-cover rounded-xl border border-[#FFD6A5]/50"
                  />
                )}
              </div>

              {/* Coordinates + Address */}
              <div className="flex flex-col gap-2">
                <label className="font-semibold text-sm text-gray-700">Location:</label>

                {address && (
                  <p className="text-xs text-gray-500 bg-[#FFF9F3] border border-[#FFD6A5]/50 rounded-md p-2">
                    📍 <b>Detected:</b> {address.split(",")[0]}
                  </p>
                )}

                <div className="flex gap-2 justify-between">
                  <input
                    type="number"
                    step="any"
                    placeholder="Latitude"
                    value={coords?.lat ?? ""}
                    onChange={(e) =>
                      setCoords({
                        ...(coords ?? { lat: 0, lng: 0 }),
                        lat: parseFloat(e.target.value),
                      })
                    }
                    className="w-[140px] border border-[#ddd] rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-[#FFADAD] focus:ring-2 focus:ring-[#FFADAD]/40 outline-none"
                  />
                  <input
                    type="number"
                    step="any"
                    placeholder="Longitude"
                    value={coords?.lng ?? ""}
                    onChange={(e) =>
                      setCoords({
                        ...(coords ?? { lat: 0, lng: 0 }),
                        lng: parseFloat(e.target.value),
                      })
                    }
                    className="w-[140px] border border-[#ddd] rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-[#FFADAD] focus:ring-2 focus:ring-[#FFADAD]/40 outline-none"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <button
                    type="button"
                    onClick={handleUseMyLocation}
                    className="text-xs text-[#FF6B6B] font-semibold underline hover:text-[#ff8585] self-start"
                  >
                    📍 Use my current location
                  </button>

                  {/* ✅ Fixed handler */}
                  <button
                    type="button"
                    onClick={handleRequestSelect}
                    className="text-xs text-[#FF6B6B] font-semibold underline hover:text-[#ff8585] self-start"
                  >
                    🗺️ Select location on map
                  </button>
                </div>
              </div>

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.97 }}
                className="w-full mt-2 bg-[#FFADAD] hover:bg-[#ff9f9f] text-[#2B2B2B] font-bold py-3 rounded-full shadow-md transition"
              >
                {loading ? "Analyzing..." : "Submit Report"}
              </motion.button>

              {/* Result */}
              {result && !result.error && (
                <div
                  className={`mt-3 text-sm font-semibold px-3 py-2 rounded-lg text-[#2B2B2B] ${
                    result.severity === "high"
                      ? "bg-[#ffadad]"
                      : result.severity === "medium"
                      ? "bg-[#FFD6A5]"
                      : "bg-[#B9FBC0]"
                  }`}
                >
                  🚧 Severity: {result.severity?.toUpperCase() || "UNKNOWN"} <br />
                  Confidence:{" "}
                  {result.confidence
                    ? `${(result.confidence * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              )}
            </form>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-[#f5f5f5] text-center text-xs text-gray-400">
              🕳️ Powered by <b>Plothole ML</b>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}