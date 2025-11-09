"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [fadeKey, setFadeKey] = useState(0);

  useEffect(() => {
    // fade overlay on route change
    setFadeKey((k) => k + 1);
  }, [pathname]);

  return (
    <div className="relative bg-[#FFF9F3] text-[#2B2B2B] transition-colors duration-500 min-h-screen">
      {/* overlay to prevent black flash */}
      <div
        key={fadeKey}
        className="fixed inset-0 bg-[#FFF9F3] z-[9999] animate-fadeOut pointer-events-none"
      />
      {children}

      <style jsx global>{`
        @keyframes fadeOut {
          from {
            opacity: 1;
          }
          to {
            opacity: 0;
          }
        }
        .animate-fadeOut {
          animation: fadeOut 0.6s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
