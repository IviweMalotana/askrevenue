/** @type {import('next').NextConfig} */
const nextConfig = {
  // We lint via the editor / CI; don't block production builds on ESLint
  // (keeps the build self-contained without the eslint plugin chain).
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
