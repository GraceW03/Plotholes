"use client";

import { useState } from "react";

type Coords = { lat: number; lng: number } | null;

export default function ReportDrawer() {
  const [file, setFile] = useState<File | null>(null);
  const [coords, setCoords] = useState<Coords>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file || !coords) {
      alert("Please select a file and location first!");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lat", String(coords.lat));
    formData.append("lng", String(coords.lng));

    try {
      const res = await fetch("/api/report", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResult(data);

      if (data.error) {
        console.error(data.error);
        alert("❌ Upload failed. Check console.");
      } else {
        alert(`✅ ${data.severity?.toUpperCase() || "UNKNOWN"} pothole detected!`);
      }
    } catch (err) {
      console.error(err);
      alert("❌ Something went wrong while uploading.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute top-4 left-4 bg-white/80 backdrop-blur-md p-4 rounded-2xl shadow-xl w-[320px] z-[1000]">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <label className="font-semibold text-sm text-gray-700">Upload a road photo:</label>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="border border-gray-300 rounded-lg p-2 text-sm"
        />

        <label className="font-semibold text-sm text-gray-700">Coordinates:</label>
        <div className="flex gap-2">
          <input
            type="number"
            step="any"
            placeholder="lat"
            value={coords?.lat ?? ""}
            onChange={(e) =>
              setCoords({
                ...(coords ?? { lat: 0, lng: 0 }),
                lat: parseFloat(e.target.value),
              })
            }
            className="flex-1 border border-gray-300 rounded-lg p-2 text-sm"
          />
          <input
            type="number"
            step="any"
            placeholder="lng"
            value={coords?.lng ?? ""}
            onChange={(e) =>
              setCoords({
                ...(coords ?? { lat: 0, lng: 0 }),
                lng: parseFloat(e.target.value),
              })
            }
            className="flex-1 border border-gray-300 rounded-lg p-2 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-2 bg-[#FFADAD] hover:bg-[#ff9f9f] text-[#2B2B2B] font-semibold py-2 rounded-full shadow transition"
        >
          {loading ? "Analyzing..." : "Submit Report"}
        </button>

        {result && !result.error && (
          <div className="mt-3 text-sm text-gray-700">
            <p>
              <b>Severity:</b> {result.severity}
            </p>
            <p>
              <b>Confidence:</b>{" "}
              {result.confidence
                ? `${(result.confidence * 100).toFixed(1)}%`
                : "N/A"}
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
