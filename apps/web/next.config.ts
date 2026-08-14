import type { NextConfig } from "next";

const internalApiOrigin = process.env.API_INTERNAL_URL ?? "http://api:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${internalApiOrigin}/api/v1/:path*`,
      },
      {
        source: "/health",
        destination: `${internalApiOrigin}/health`,
      },
    ];
  },
};

export default nextConfig;
