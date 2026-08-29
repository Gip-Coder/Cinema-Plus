import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const nextConfig: NextConfig = {
  outputFileTracingRoot: process.cwd(),
  reactStrictMode: true,
  // Allow poster images from local backend and common CDN sources
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
      },
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  webpack: (config, { dev, isServer }) => {
    // Only enable React profiling when REACT_PROFILE=true is set.
    // Profiling builds are ~15-20% slower and should NEVER be the default in production.
    if (!dev && !isServer && process.env.REACT_PROFILE === "true") {
      config.resolve.alias = {
        ...config.resolve.alias,
        "react-dom$": "react-dom/profiling",
        "scheduler/tracing": "scheduler/tracing-profiling",
      };
    }
    return config;
  },
};

// Bundle analyzer — only active when ANALYZE=true
const withBundleAnalyzer =
  process.env.ANALYZE === "true"
    ? bundleAnalyzer({ enabled: true })
    : (c: NextConfig) => c;

export default withBundleAnalyzer(nextConfig);
