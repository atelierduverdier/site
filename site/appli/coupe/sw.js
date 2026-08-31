// Service worker : met l'appli en cache pour un fonctionnement hors-ligne
// complet. Pour publier une mise à jour : INCRÉMENTER la version ci-dessous
// (coupe-v2 -> coupe-v3 ...) — sans quoi les visiteurs gardent l'ancienne
// version, servie par leur propre cache. Le navigateur recompare ce fichier
// à chaque visite : c'est lui qui déclenche le renouvellement.
const CACHE = "coupe-v19";
const PORTEE = new URL("./", self.location).pathname;
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon.svg",
  "./icon-180.png",
  "./icon-192.png",
  "./icon-512.png"
];

self.addEventListener("install", function(e){
  e.waitUntil(
    caches.open(CACHE).then(function(c){ return c.addAll(ASSETS); })
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(k){ return k !== CACHE; })
        .map(function(k){ return caches.delete(k); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function(e){
  if(e.request.method !== "GET") return;
  // Même origine seulement : le compteur de fréquentation change d'adresse
  // à chaque appel, le mettre en cache ferait grossir celui-ci sans fin.
  const url = new URL(e.request.url);
  if(url.origin !== self.location.origin) return;
  // version.json part TOUJOURS au réseau, jamais par ici : c'est le fichier
  // qui dit quelle version est en ligne. Servi depuis le cache, il
  // comparerait la version installée à elle-même et répondrait « à jour »
  // pour l'éternité — exactement le contraire de ce qu'on lui demande.
  if(url.pathname.endsWith("/version.json")) return;
  // Ne garder QUE ce qui appartient a l'appli, et sans parametres. Sans ces
  // deux lignes, le cache de l'appli avalait des pages du site entier
  // (verifie le 24/08 : /, /logiciels/*, /projets/* s'y trouvaient) ainsi
  // qu'une entree par adresse a rallonge — ?maj=..., ?utm=... Rien de tout
  // cela n'a vocation a etre servi hors-ligne par l'appli.
  if(!url.pathname.startsWith(PORTEE)) return;
  if(url.search) return;
  e.respondWith(
    caches.match(e.request).then(function(hit){
      return hit || fetch(e.request).then(function(resp){
        var copy = resp.clone();
        caches.open(CACHE).then(function(c){ c.put(e.request, copy); });
        return resp;
      }).catch(function(){ return caches.match("./index.html"); });
    })
  );
});
