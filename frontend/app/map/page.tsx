"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const NYCMap = dynamic(() => import("@/components/NYCMap"), {
  ssr: false,
});

export default function MapPage() {
  const [fadeIn, setFadeIn] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setFadeIn(true), 50); // delay ensures CSS triggers
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      className={`h-screen w-screen bg-[#FFF9F3] relative overflow-hidden transition-opacity duration-700 ease-in-out ${
        fadeIn ? "opacity-100" : "opacity-0"
      }`}
    >
      <NYCMap />
    </div>
  );
}
