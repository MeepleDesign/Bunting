/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // The demo itself is a static page built from prototype/bunting.html.
    return { beforeFiles: [{ source: '/', destination: '/bunting.html' }] };
  },
  async headers() {
    return [{ source: '/bunting.html', headers: [{ key: 'Cache-Control', value: 'no-cache' }] }];
  },
};
export default nextConfig;
