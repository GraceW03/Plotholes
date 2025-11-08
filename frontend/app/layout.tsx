import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Plothole",
  description: "Mapping potholes across NYC — one bump at a time.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
