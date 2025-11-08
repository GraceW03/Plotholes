"use client";

import dynamic from "next/dynamic";
import UploadBox from "@/components/UploadBox";
import ReportDrawer from "@/components/ReportDrawer";

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
    <div className="h-[70vh] w-full">
        <NYCMap />
        <ReportDrawer />
    </div>
  );
}
