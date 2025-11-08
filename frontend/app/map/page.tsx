"use client";

import dynamic from "next/dynamic";

const NYCMap = dynamic(() => import("@/components/NYCMap"), {
  ssr: false,
  loading: () => (
    <div className="h-screen w-screen flex items-center justify-center bg-[#FFF9F3] text-lg font-semibold text-[#2B2B2B]">
      🗺️ Loading NYC Plothole Map...
    </div>
  ),
});

export default function MapPage() {
  return (
<<<<<<< HEAD
    <div className="h-screen w-full relative">
      <NYCMap />
      <ReportDrawer />
=======
    <div className="h-screen w-full">
      <NYCMap />
>>>>>>> c839520cab61fba866086f63098057a3631cdf23
    </div>
  );
}