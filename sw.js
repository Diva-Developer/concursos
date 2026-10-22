/* Modo offline do app: páginas e dados do próprio site vêm da rede quando há internet
   (e ficam guardados); sem internet, abre a última versão guardada. Fontes do Google ficam em cache. */
const CACHE = "concursos-pbpe-v1";
const BASICO = ["./", "./index.html", "./app.json", "./manifest.webmanifest", "./icones/icon-192.png", "./icones/apple-touch-icon.png"];

self.addEventListener("install", ev => {
  self.skipWaiting();
  ev.waitUntil(caches.open(CACHE).then(c => c.addAll(BASICO)).catch(() => {}));
});

self.addEventListener("activate", ev => {
  ev.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("message", ev => {
  if (ev.data === "limpar") caches.delete(CACHE);
});

self.addEventListener("fetch", ev => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    ev.respondWith(
      fetch(req).then(res => {
        if (res.ok && !url.search) { const copia = res.clone(); caches.open(CACHE).then(c => c.put(req, copia)); }
        return res;
      }).catch(() => caches.match(req, {ignoreSearch: true}).then(r => r || caches.match("./index.html")))
    );
  } else if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {
    ev.respondWith(caches.match(req).then(r => r || fetch(req).then(res => {
      const copia = res.clone(); caches.open(CACHE).then(c => c.put(req, copia)); return res;
    })));
  }
});
