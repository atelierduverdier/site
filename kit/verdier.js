/* =========================================================================
   verdier.js — comportements communs de la charte Atelier du Verdier
   =========================================================================
   FICHIER DU KIT, recopié dans chaque site par outils/diffuser_kit.py.
   Ne pas l'éditer dans une copie : elle sera écrasée.
   Source : atelierduverdier/site — kit/verdier.js

   Trois choses seulement : la bascule de thème, la visionneuse d'images,
   et l'apparition au défilement.
   Tout est défensif — chaque site ne contient pas forcément les deux, et
   un kit partagé qui plante sur une page sans bouton casserait TOUTES les
   pages qui suivent dans le même fichier.
   ========================================================================= */

/* ---------- Thème clair / sombre ----------------------------------------
   Le choix est rangé dans un COOKIE, pas dans localStorage, et c'est
   volontaire : localStorage est cloisonné par origine, donc un réglage
   fait sur atelierduverdier.fr ne suivrait pas le visiteur sur
   laser.atelierduverdier.fr. Le cookie est posé sur le domaine parent, il
   traverse les sous-domaines.

   Pas de bandeau de consentement à prévoir pour autant : mémoriser un
   choix d'affichage exprimé par l'utilisateur lui-même fait partie des
   cas que la CNIL dispense de consentement. Aucun traçage, aucun tiers.

   Le repli sur localStorage sert au développement en local (file://),
   où un cookie de domaine ne peut pas être posé. */

(function(){
  var CLE = 'verdier-theme';
  var root = document.documentElement;

  function domaineParent(){
    var h = location.hostname || '';
    var m = h.match(/([^.]+\.[^.]+)$/);          // « laser.x.fr » -> « x.fr »
    return (h && h !== 'localhost' && m) ? '; domain=.' + m[1] : '';
  }

  function lire(){
    var m = document.cookie.match(/(?:^|;\s*)verdier-theme=(light|dark)/);
    if (m) return m[1];
    try { return localStorage.getItem(CLE); } catch(e) { return null; }
  }

  function ecrire(v){
    try {
      document.cookie = CLE + '=' + v + '; path=/; max-age=31536000; SameSite=Lax' + domaineParent();
    } catch(e) {}
    try { localStorage.setItem(CLE, v); } catch(e) {}
  }

  function courant(){
    var a = root.getAttribute('data-theme');
    if (a) return a;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  var choisi = lire();
  if (choisi) root.setAttribute('data-theme', choisi);

  // Plusieurs boutons possibles (en-tête + pied) : on les câble tous.
  var boutons = document.querySelectorAll('.theme-btn');
  for (var i = 0; i < boutons.length; i++){
    boutons[i].addEventListener('click', function(){
      var suivant = courant() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', suivant);
      ecrire(suivant);
    });
  }
})();

/* ---------- Menu en étroit ----------------------------------------------
   Sous 860 px la barre de navigation est repliée derrière un bouton. Le CSS
   fait tout l'affichage ; le JS ne pose qu'une classe et tient
   aria-expanded à jour pour les lecteurs d'écran. */

(function(){
  var btn = document.querySelector('.nav-btn');
  var nav = document.querySelector('.navlinks');
  if (!btn || !nav) return;

  function replier(){
    nav.classList.remove('ouvert');
    btn.setAttribute('aria-expanded', 'false');
  }

  btn.setAttribute('aria-expanded', 'false');

  btn.addEventListener('click', function(e){
    e.stopPropagation();
    var ouvert = nav.classList.toggle('ouvert');
    btn.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
  });

  // Un clic sur un lien, ailleurs, ou Échap referme.
  nav.addEventListener('click', function(e){ if (e.target.tagName === 'A') replier(); });
  document.addEventListener('click', replier);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') replier(); });
})();

/* ---------- Visionneuse d'images ----------------------------------------
   S'active sur [data-agrandir], et sur les deux sélecteurs historiques du
   site laser — au chantier 3 le kit remplacera son script en place, il ne
   doit rien lui retirer au passage. */

(function(){
  var lb = document.getElementById('lightbox');
  if (!lb) return;                                  // page sans visionneuse

  var img   = document.getElementById('lbImg');
  var close = document.getElementById('lbClose');
  if (!img) return;

  function ouvrir(src, alt){
    img.src = src; img.alt = alt || '';
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function fermer(){
    lb.classList.remove('open'); img.src = '';
    document.body.style.overflow = '';
  }

  var cibles = document.querySelectorAll('[data-agrandir], .mode .shot img, .diagram img');
  for (var i = 0; i < cibles.length; i++){
    (function(el){
      el.style.cursor = 'zoom-in';
      el.addEventListener('click', function(){ ouvrir(el.currentSrc || el.src, el.alt); });
    })(cibles[i]);
  }

  lb.addEventListener('click', fermer);
  if (close) close.addEventListener('click', function(e){ e.stopPropagation(); fermer(); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') fermer(); });
})();


/* ---------- Apparition au défilement -------------------------------------
   Les blocs montent doucement en entrant dans le champ, au lieu d'être
   tous là d'emblée.

   LE POINT QUI COMPTE : la classe qui rend un bloc invisible est posée
   ICI, par le script, et seulement après avoir vérifié que le navigateur
   sait l'animer. Écrite dans le HTML, elle aurait laissé une page BLANCHE
   à qui bloque le JavaScript — c'est le piège classique de ce genre
   d'effet, et il ne pardonne pas sur un site de documentation.

   Rien n'est observé au-dessus de la ligne de flottaison : un bloc déjà
   visible au chargement doit l'être tout de suite, pas se mettre à bouger
   sous les yeux du visiteur.

   Le décalage entre voisins (60 ms) donne le petit ruissellement d'une
   rangée de cartes. Au-delà de six, on arrête de décaler : sur une longue
   liste, l'attente se verrait. */

(function(){
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var SELECTEUR = [
    'section .sec-tag', 'section > .wrap > h2', 'section > .wrap > .sec-lede',
    'section > .wrap > p', 'section > .wrap > h3',
    '.carte', '.panel', '.figure', '.plan', '.capture',
    '.callout', '.step', '.cols > *', '.liens'
  ].join(',');

  var blocs = [].slice.call(document.querySelectorAll(SELECTEUR));
  if (!blocs.length) return;

  var haut = window.innerHeight || 800;
  var obs = new IntersectionObserver(function(entrees){
    for (var i = 0; i < entrees.length; i++){
      if (!entrees[i].isIntersecting) continue;
      var el = entrees[i].target;
      var rang = +el.getAttribute('data-rang') || 0;
      el.style.transitionDelay = (rang * 60) + 'ms';
      el.classList.add('vu');
      obs.unobserve(el);                     // une fois vu, on n'y revient pas
    }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

  var precedent = null, rang = 0;
  for (var i = 0; i < blocs.length; i++){
    var el = blocs[i];
    if (el.getBoundingClientRect().top < haut * 0.9) continue;   // déjà à l'écran
    rang = (el.parentNode === precedent) ? Math.min(rang + 1, 5) : 0;
    precedent = el.parentNode;
    el.setAttribute('data-rang', rang);
    el.classList.add('js-reveal');
    obs.observe(el);
  }
})();
