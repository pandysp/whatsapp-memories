import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env file from the ROOT directory (two levels up)
const envPath = path.resolve(__dirname, '../../.env');
console.log('[next.config.mjs] Attempting to load .env from:', envPath);
dotenv.config({ path: envPath, override: true });

// Verify if the variables are loaded within the config file
console.log('[next.config.mjs] KV_REST_API_URL loaded:', process.env.KV_REST_API_URL ? 'Yes' : 'No');
console.log('[next.config.mjs] KV_REST_API_TOKEN loaded:', process.env.KV_REST_API_TOKEN ? 'Yes (masked)' : 'No'); // Mask token in logs

let userConfig = undefined
try {
  // try to import ESM first
  userConfig = await import('./v0-user-next.config.mjs')
} catch (e) {
  try {
    // fallback to CJS import
    userConfig = await import("./v0-user-next.config");
  } catch (innerError) {
    // ignore error
  }
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Optional: Explicitly expose necessary env vars (especially for client-side)
  // Remember: Only vars starting with NEXT_PUBLIC_ are exposed to the browser.
  // Server-side vars loaded here are available during build and server runtime.
  env: {
    // Example: If you need KV_URL client-side (NOT RECOMMENDED FOR SECRETS)
    // NEXT_PUBLIC_KV_URL: process.env.KV_URL,
    // Example: If you have a non-secret variable needed client-side
    // NEXT_PUBLIC_API_ENDPOINT: process.env.API_ENDPOINT_FROM_ROOT_ENV,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    webpackBuildWorker: true,
    parallelServerBuildTraces: true,
    parallelServerCompiles: true,
  },
}

if (userConfig) {
  // ESM imports will have a "default" property
  const config = userConfig.default || userConfig

  for (const key in config) {
    if (
      typeof nextConfig[key] === 'object' &&
      !Array.isArray(nextConfig[key])
    ) {
      nextConfig[key] = {
        ...nextConfig[key],
        ...config[key],
      }
    } else {
      nextConfig[key] = config[key]
    }
  }
}

export default nextConfig
