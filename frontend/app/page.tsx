"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { MapPin, Hammer, Sparkles, Building2 } from "lucide-react";
import confetti from "canvas-confetti";

export default function Home() {
  const handleConfetti = () => {
    confetti({
      particleCount: 120,
      spread: 80,
      origin: { y: 0.6 },
      colors: ["#FFADAD", "#FFD6A5", "#B9FBC0", "#CDB4DB"],
    });
  };

  return (
    <div className="min-h-screen flex flex-col items-center overflow-hidden relative bg-[#FFF9F3] text-[#2B2B2B]">
      {/* soft pastel blobs */}
      <div className="absolute top-[-60px] left-[-40px] w-72 h-72 bg-[#FFD6A5]/60 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-[-80px] right-[-50px] w-96 h-96 bg-[#B9FBC0]/60 rounded-full blur-3xl animate-pulse" />

      {/* NAVBAR */}
      <nav className="z-10 w-full flex justify-between items-center px-10 py-6">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 120 }}
          className="flex items-center gap-3"
        >
          <Building2 className="w-7 h-7 text-[#FF6B6B]" />
          <h1 className="text-3xl font-extrabold">Plothole</h1>
        </motion.div>
        <a
          href="https://github.com/GraceW03/Plotholes"
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-full bg-white/80 backdrop-blur px-5 py-2 text-sm font-semibold shadow hover:scale-105 transition"
        >
          ⭐ GitHub
        </a>
      </nav>

      {/* HERO */}
      <main className="relative flex flex-col items-center text-center px-6 pt-16 pb-20 max-w-2xl z-10">
        <motion.h2
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, type: "spring" }}
          className="text-6xl md:text-7xl font-extrabold leading-tight mb-6"
        >
          Patch. Plot. Play. <br />
          Welcome to <span className="text-[#FF6B6B] drop-shadow-sm">Plothole</span> 🕳️
        </motion.h2>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-lg text-[#555] mb-12 max-w-md"
        >
          A playful map of every bump, fix, and funky road in NYC — turning civic
          data into a little adventure.
        </motion.p>

        {/* squiggly road + moving car */}
        {/* <div className="absolute -z-10 top-[62%] left-1/2 -translate-x-1/2 w-[460px] h-[150px] pointer-events-none">
          <svg
            viewBox="0 0 460 150"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            className="w-full h-full"
          >
            <defs>
              <linearGradient id="roadGradient" x1="0" y1="0" x2="460" y2="0">
                <stop offset="0%" stopColor="#FFADAD" />
                <stop offset="50%" stopColor="#FFD6A5" />
                <stop offset="100%" stopColor="#B9FBC0" />
              </linearGradient>
              <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <path
              id="plotholePath"
              d="M10,110 C70,45 150,40 210,95 C270,150 350,135 450,70"
              stroke="url(#roadGradient)"
              strokeWidth="3.5"
              strokeDasharray="8 9"
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity="0.9"
              filter="url(#softGlow)"
            />

            {[0.1, 0.25, 0.4].map((delay, i) => (
              <circle key={i} r="2.6" fill="#FFADAD" opacity={0.6 - i * 0.18}>
                <animateMotion
                  dur="7s"
                  repeatCount="indefinite"
                  rotate="auto"
                  begin={`${delay * 7}s`}
                >
                  <mpath href="#plotholePath" xlinkHref="#plotholePath" />
                </animateMotion>
              </circle>
            ))} */}

            {/* car */}
            {/* <g id="carIcon" transform="scale(1)">
              <g transform="translate(-18,-14)">
                <path
                  d="M6 10 C6 5 10 2 15 2 H24 C28 2 32 5 33 9 L35 16 C35 18 34 19 32 19 H10 C8 19 7 18 7 16 Z"
                  fill="#ff6b6b"
                />
                <path
                  d="M16 4 H24 C26 4 28 6 28 8 V11 H14 V6 C14 5 15 4 16 4 Z"
                  fill="#9bd7ff"
                />
                <rect
                  x="6"
                  y="16.5"
                  width="6"
                  height="2"
                  rx="1"
                  fill="#c94b4b"
                />
                <circle cx="12" cy="20" r="4" fill="#222" />
                <circle cx="28" cy="20" r="4" fill="#222" />
                <circle cx="12" cy="20" r="2" fill="#666" />
                <circle cx="28" cy="20" r="2" fill="#666" />
              </g>

              <animateMotion dur="7s" repeatCount="indefinite" rotate="auto">
                <mpath href="#plotholePath" xlinkHref="#plotholePath" />
              </animateMotion>
            </g>
          </svg>
        </div> */}

        {/* CTA */}
        <motion.div whileHover={{ scale: 1.05 }}>
          <Link
            href="/map"
            onClick={handleConfetti}
            className="inline-flex items-center gap-3 rounded-full bg-[#FFADAD] hover:bg-[#ff9f9f] text-[#2B2B2B] font-bold px-10 py-4 text-lg shadow-md transition"
          >
            <MapPin className="w-6 h-6" />
            Explore the Map
          </Link>
        </motion.div>
      </main>

      {/* STORY STRIP — full-width playful road timeline */}
      <section className="relative w-full px-10 py-10 flex flex-col items-center overflow-hidden">
        {/* full-width curved road with car ABOVE content */}
        <svg
          viewBox="0 0 1600 160"
          xmlns="http://www.w3.org/2000/svg"
          className="absolute top-[8%] left-1/2 -translate-x-1/2 w-[1600px] max-w-none opacity-80 z-0"
        >
          <defs>
            <linearGradient id="roadGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FF8FA3" />
              <stop offset="50%" stopColor="#FFB88C" />
              <stop offset="100%" stopColor="#A8E6CF" />
            </linearGradient>
          </defs>
          <path
            id="timelineRoad"
            d="M0,80 C250,25 500,130 800,60 C1100,10 1350,150 1600,80"
            stroke="url(#roadGradient)"
            strokeWidth="10"
            strokeDasharray="18 14"
            fill="none"
            strokeLinecap="round"
            opacity="0.8"
          />

          {/* 🚗 car driving full-width above details */}
          <g id="carIcon" transform="scale(1)">
            <g transform="translate(-18,-14)">
              <path
                d="M6 10 C6 5 10 2 15 2 H24 C28 2 32 5 33 9 L35 16 C35 18 34 19 32 19 H10 C8 19 7 18 7 16 Z"
                fill="#FF6B6B"
              />
              <path
                d="M16 4 H24 C26 4 28 6 28 8 V11 H14 V6 C14 5 15 4 16 4 Z"
                fill="#9BD7FF"
              />
              <circle cx="12" cy="20" r="4" fill="#222" />
              <circle cx="28" cy="20" r="4" fill="#222" />
              <circle cx="12" cy="20" r="2" fill="#666" />
              <circle cx="28" cy="20" r="2" fill="#666" />
            </g>

            <animateMotion dur="15s" repeatCount="indefinite" rotate="auto">
              <mpath href="#timelineRoad" />
            </animateMotion>
          </g>
        </svg>

        {/* milestones anchored below road */}
        <div className="relative flex justify-between items-start w-full max-w-5xl z-10">
          <FeatureStop
            color="#FFB88C"
            icon={<MapPin className="w-8 h-8 text-[#FF6B6B]" />}
            title="Spot it 👀"
            desc="Tag every bump you find — each pin adds to NYC’s pothole adventure."
          />
          <FeatureStop
            color="#A8E6CF"
            icon={<Hammer className="w-8 h-8 text-[#2B2B2B]" />}
            title="Fix it 🧰"
            desc="Watch repairs roll in and track progress across boroughs."
          />
          <FeatureStop
            color="#C5A3E0"
            icon={<Sparkles className="w-8 h-8 text-[#2B2B2B]" />}
            title="Love it 💖"
            desc="Celebrate smoother rides and leaderboard legends with confetti!"
          />
        </div>
      </section>

      {/* FOOTER */}
      <footer className="w-full text-center py-8 text-sm text-[#777] z-10">
        Built at <span className="font-semibold">HackUMass 2025</span> • Made with 🍨 & 💖 by Jillian, Grace, and Elaine
      </footer>
    </div>
  );
}

function FeatureStop({
  color,
  icon,
  title,
  desc,
}: {
  color: string;
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <motion.div
      whileHover={{ scale: 1.1 }}
      transition={{ type: "spring", stiffness: 250 }}
      className="flex flex-col items-center text-center max-w-[200px] space-y-3"
    >
      <div
        className="p-5 rounded-full shadow-md"
        style={{ backgroundColor: color }}
      >
        {icon}
      </div>
      <h3 className="text-lg font-bold">{title}</h3>
      <p className="text-sm text-[#444] leading-snug">{desc}</p>
    </motion.div>
  );
}
