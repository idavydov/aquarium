import assert from 'node:assert/strict';
import {readFile, readdir} from 'node:fs/promises';
import {afterEach, mock, test} from 'node:test';
import {createRandomWorker} from './random_worker.mjs';

afterEach(() => mock.restoreAll());

const paths = ['/аккорды/Первый', '/аккорды/Второй'];
const worker = createRandomWorker(paths);
const assets = {
  fetch: async request => new Response(new URL(request.url).pathname,
    {headers: {'ETag': 'old-song', 'Last-Modified': 'yesterday', 'Cache-Control': 'public'}})
};

test('missing or wrong switch returns an uncached 404', async () => {
  for (const query of ['', '?r=', '?r=no', '?other=r']) {
    const response = await worker.fetch(new Request('https://example.com/r' + query), {ASSETS: assets});
    assert.equal(response.status, 404);
    assert.equal(await response.text(), '/404.html');
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.equal(response.headers.get('x-robots-tag'), 'noindex, nofollow');
  }
});

test('each request makes a new selection without redirects or conditional asset requests', async () => {
  let next = 0;
  mock.method(Math, 'random', () => next++ === 0 ? 0 : 0.999);
  const requested = [];
  const env = {ASSETS: {fetch: async request => {
    requested.push(request);
    return assets.fetch(request);
  }}};
  for (const path of paths) {
    const request = new Request('https://example.com/r?r=r', {headers: {'If-None-Match': 'old-song'}});
    const response = await worker.fetch(request, env);
    assert.equal(response.status, 200);
    assert.equal(await response.text(), new URL(path, request.url).pathname);
    assert.equal(response.headers.get('location'), null);
    assert.equal(response.headers.get('etag'), null);
    assert.equal(response.headers.get('last-modified'), null);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.equal(request.url, 'https://example.com/r?r=r');
  }
  assert.ok(requested.every(request => !request.headers.has('if-none-match')));
});

test('HEAD has no body; unsupported methods do not reveal a song', async () => {
  const head = await worker.fetch(new Request('https://example.com/r?r=r', {method: 'HEAD'}), {ASSETS: assets});
  assert.equal(head.status, 200);
  assert.equal(await head.text(), '');
  const post = await worker.fetch(new Request('https://example.com/r?r=r', {method: 'POST'}), {ASSETS: assets});
  assert.equal(post.status, 404);
});

test('normal pages pass through with their cache headers intact', async () => {
  const request = new Request('https://example.com/css/archive.css');
  const response = await worker.fetch(request, {ASSETS: assets});
  assert.equal(await response.text(), '/css/archive.css');
  assert.equal(response.headers.get('cache-control'), 'public');
  assert.equal(response.headers.get('x-robots-tag'), null);
});

test('an unavailable song never redirects to another URL', async () => {
  mock.method(console, 'error', () => {});
  const env = {ASSETS: {fetch: async () => new Response(null,
    {status: 302, headers: {'Location': '/somewhere', 'Content-Length': '1000'}})}};
  const response = await worker.fetch(new Request('https://example.com/r?r=r'), env);
  assert.equal(response.status, 502);
  assert.equal(response.headers.get('location'), null);
  assert.equal(response.headers.get('content-length'), null);
  assert.equal(await response.text(), 'Song unavailable');
});

test('generated worker includes every song and executes with actual generated HTML', async () => {
  const source = await readFile(new URL('../public/_worker.js', import.meta.url), 'utf8');
  const catalog = JSON.parse(source.match(/export default createRandomWorker\((\[.*\])\);/)[1]);
  const names = await readdir(new URL('../public/аккорды/', import.meta.url));
  const expected = names.filter(name => name.endsWith('.html'))
    .map(name => '/аккорды/' + name.slice(0, -5)).sort();
  assert.deepEqual(catalog.map(decodeURIComponent).sort(), expected);
  assert.equal(new Set(catalog).size, expected.length);
  const built = (await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'))).default;
  mock.method(Math, 'random', () => 0);
  const env = {ASSETS: {fetch: async request => {
    const path = decodeURIComponent(new URL(request.url).pathname);
    return new Response(await readFile(new URL('../public' + path + '.html', import.meta.url)),
      {headers: {'Content-Type': 'text/html; charset=utf-8'}});
  }}};
  const response = await built.fetch(new Request('https://example.com/r?r=r'), env);
  assert.equal(response.status, 200);
  assert.match(await response.text(), /<article class="song-content"/);
  const routes = JSON.parse(await readFile(new URL('../public/_routes.json', import.meta.url)));
  assert.deepEqual(routes, {version: 1, include: ['/r'], exclude: []});
  for (const file of ['index.html', 'sitemap.xml', 'robots.txt']) {
    assert.doesNotMatch(await readFile(new URL('../public/' + file, import.meta.url), 'utf8'), /["'>\s]\/r(?:[?<\s"']|$)/);
  }
});
