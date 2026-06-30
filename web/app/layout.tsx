import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AskRevenue — natural-language analytics",
  description:
    "Ask plain-English questions about a subscription business and get safe SQL, charts, and answers.",
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
