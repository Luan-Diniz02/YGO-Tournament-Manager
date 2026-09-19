// Service Worker - Liga YGO Marabá
const CACHE_NAME = 'ygo-cache-v1';

const PRECACHE_RESOURCES = [
  '/',
  '/static/css/style.css',
  '/static/js/script.js',
  '/static/manifest.json',
  '/static/icons/icon.svg',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// Instalação do Service Worker e pré-cache dos recursos essenciais
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(PRECACHE_RESOURCES).catch((err) => {
          console.warn('[SW] Aviso: Alguns recursos não puderam ser pré-cacheados:', err);
        });
      })
      .then(() => self.skipWaiting())
  );
});

// Ativação e limpeza de caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Interceptação de requisições
self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Apenas intercepta requisições GET
  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  // Ignora chamadas de esquemas não HTTP/HTTPS (como chrome-extension)
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Requisição de Navegação / Páginas HTML: Network-first
  const isHtmlRequest = request.mode === 'navigate' || 
                        (request.headers.get('accept') && request.headers.get('accept').includes('text/html'));

  if (isHtmlRequest) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return networkResponse;
        })
        .catch(async () => {
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          // Tenta a página raiz pré-cacheada caso offline
          const cachedHome = await caches.match('/');
          if (cachedHome) {
            return cachedHome;
          }
          return new Response('Página indisponível offline.', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({ 'Content-Type': 'text/plain; charset=utf-8' })
          });
        })
    );
    return;
  }

  // Recursos estáticos essenciais (CSS, JS, fontes, ícones, imagens): Stale-While-Revalidate / Cache-first
  const isStaticResource = url.pathname.startsWith('/static/') ||
                           url.hostname.includes('fonts.googleapis.com') ||
                           url.hostname.includes('fonts.gstatic.com') ||
                           url.hostname.includes('cdnjs.cloudflare.com') ||
                           url.hostname.includes('cdn.jsdelivr.net');

  if (isStaticResource) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return networkResponse;
          })
          .catch(() => cachedResponse);

        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // Comportamento padrão: busca da rede
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
