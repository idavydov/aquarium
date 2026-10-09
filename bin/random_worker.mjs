/* Bundled with the song paths by bin/build.py for Cloudflare Pages. */
export function createRandomWorker(songPaths) {
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (url.pathname !== '/r') return env.ASSETS.fetch(request);

      const valid = url.searchParams.get('r') === 'r'
        && (request.method === 'GET' || request.method === 'HEAD');
      const path = valid ? songPaths[Math.floor(Math.random() * songPaths.length)] : '/404.html';
      const assetUrl = new URL(path, url.origin);
      // Do not forward conditional headers: each reload must render a fresh
      // selection rather than reusing the previous random response via a 304.
      const asset = await env.ASSETS.fetch(new Request(assetUrl));
      const headers = new Headers(asset.headers);
      headers.set('Cache-Control', 'no-store');
      headers.set('X-Robots-Tag', 'noindex, nofollow');
      for (const name of ['ETag', 'Last-Modified', 'Age', 'Location', 'Content-Length']) headers.delete(name);
      if (valid && asset.status !== 200) {
        console.error(JSON.stringify({event: 'random-song-asset-error', path, status: asset.status}));
        return new Response('Song unavailable', {status: 502, headers});
      }
      return new Response(request.method === 'HEAD' ? null : asset.body,
        {status: valid ? 200 : 404, headers});
    }
  };
}
