/**
 * Static-demo mode (build with VITE_STATIC_DEMO=true).
 *
 * The dashboard normally talks to the FastAPI backend. For a shareable read-only build,
 * scripts/export_static_demo.py saves the backend's own responses as files next to the page,
 * and this module maps each backend route to the matching relative file. Live upload is
 * answered with a clear 503 because the deterministic pipeline does not run in a browser.
 */

export const IS_STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === 'true';

export const STATIC_DEMO_UPLOAD_MESSAGE =
  'Live analysis needs the Python backend. This shared demo shows pre-computed pipeline results only.';

const ROUTES: Array<[RegExp, (m: RegExpMatchArray) => string]> = [
  [/^\/samples\/?$/, () => 'api/samples.json'],
  [/^\/api\/references\/?$/, () => 'api/references.json'],
  [/^\/api\/benchmark\/?$/, () => 'api/benchmark.json'],
  [/^\/results\/([A-Za-z0-9_-]+)$/, (m) => `api/results/${m[1]}.json`],
  [/^\/api\/audio\/([A-Za-z0-9_-]+\.wav)$/, (m) => `audio/${m[1]}`],
];

/** Maps a backend route to its static file. Returns the input unchanged outside static mode. */
export function resolveApiUrl(path: string, staticMode: boolean = IS_STATIC_DEMO): string {
  if (!staticMode) return path;
  for (const [pattern, toFile] of ROUTES) {
    const m = path.match(pattern);
    if (m) return toFile(m);
  }
  return path;
}

export function installStaticApi(): void {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.pathname : input.url;
    if (url.startsWith('/analyze') || url.startsWith('/jobs/')) {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: STATIC_DEMO_UPLOAD_MESSAGE }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    }
    const mapped = resolveApiUrl(url, true);
    return originalFetch(mapped === url ? input : mapped, init);
  };
}
