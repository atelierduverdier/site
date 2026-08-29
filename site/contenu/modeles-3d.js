/* =======================================================================
   modeles-3d.js — plein écran et réglages d'éclairage des vues 3D
   =======================================================================
   Christophe, 29/08/2026 : « c'est tout petit » et « on peut ajouter des
   paramètres pour changer l'éclairage ou autre ? ». Les deux tiennent ici.

   UN SEUL JEU DE RÉGLAGES POUR TOUTE LA PAGE, et c'était la condition pour
   que ça vaille la peine : quatre curseurs à refaire glisser sous chaque
   vignette, personne ne s'en sert deux fois. On règle une fois, les quatre
   objets suivent.

   RIEN N'EST ÉCRIT DANS LE CONTENU. Ni le bouton, ni les curseurs : tout est
   posé par ce script. Là où le plein écran n'existe pas — iOS le refuse sur
   un élément quelconque — le bouton n'apparaît pas, et personne ne clique sur
   un bouton mort. Sans JavaScript, la page reste exactement ce qu'elle est
   aujourd'hui : quatre objets à faire tourner à la souris.
   ======================================================================= */
(function () {
  var vues = Array.prototype.slice.call(
    document.querySelectorAll('.cartes-3d model-viewer'));
  if (!vues.length) return;

  /* ---- 1. Plein écran ------------------------------------------------ */
  vues.forEach(function (v) {
    if (!v.requestFullscreen) return;
    var b = document.createElement('button');
    b.className = 'plein-ecran';
    b.type = 'button';
    b.textContent = '⤢ plein écran';
    b.title = 'Agrandir cet objet à tout l’écran';
    b.addEventListener('click', function () { v.requestFullscreen(); });
    v.parentNode.insertBefore(b, v);
  });

  /* ---- 2. Les réglages ------------------------------------------------
     LES DÉFAUTS SONT CEUX DU BALISAGE, pas des constantes écrites ici. Les
     <model-viewer> portent déjà leur exposition et leur ombre ; « remettre
     à zéro » doit rendre EXACTEMENT ce que la page sert sans JavaScript, et
     deux jeux de valeurs à tenir d'accord finiraient par diverger. */
  var DEFAUTS = {
    expo: parseFloat(vues[0].getAttribute('exposure')) || 1,
    ombre: parseFloat(vues[0].getAttribute('shadow-intensity')) || 0,
    tourne: vues[0].hasAttribute('auto-rotate')
  };

  /* localStorage et non un cookie, contrairement au thème : celui-ci doit
     traverser les quatre sous-domaines, ce réglage-ci ne concerne qu'une
     page d'un seul domaine. Il n'a rien à traverser. */
  var CLE = 'verdier-3d';
  function lire() {
    try { return JSON.parse(localStorage.getItem(CLE)) || {}; }
    catch (e) { return {}; }
  }
  function ecrire() {
    try { localStorage.setItem(CLE, JSON.stringify(etat)); } catch (e) {}
  }

  var garde = lire();
  /* LE RÉGLAGE SYSTÈME GOUVERNE LE DÉFAUT, LE CLIC GOUVERNE LE RESTE. La
     rotation est allumée d'origine depuis le 29/08/2026 ; on ne l'impose donc
     pas à qui a demandé moins d'animations à son système — mais s'il l'a
     cochée lui-même, c'est un choix explicite et il tient. Sans stockage, on
     retombe sur le défaut, corrigé du réglage système. */
  var reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var etat = {
    expo: typeof garde.expo === 'number' ? garde.expo : DEFAUTS.expo,
    ombre: typeof garde.ombre === 'number' ? garde.ombre : DEFAUTS.ombre,
    tourne: typeof garde.tourne === 'boolean' ? garde.tourne
                                             : (DEFAUTS.tourne && !reduit)
  };

  function appliquer() {
    vues.forEach(function (v) {
      v.setAttribute('exposure', etat.expo);
      v.setAttribute('shadow-intensity', etat.ombre);
      if (etat.tourne) { v.setAttribute('auto-rotate', ''); }
      else { v.removeAttribute('auto-rotate'); }
    });
  }

  function curseur(nom, cle, min, max, pas, unite) {
    var l = document.createElement('label');
    l.className = 'reglage';
    var t = document.createElement('span');
    t.className = 'titre';
    var i = document.createElement('input');
    i.type = 'range';
    i.min = min; i.max = max; i.step = pas; i.value = etat[cle];
    function dire() { t.textContent = nom + ' : ' + (+etat[cle]).toFixed(2) + (unite || ''); }
    i.addEventListener('input', function () {
      etat[cle] = parseFloat(i.value); dire(); appliquer(); ecrire();
    });
    dire();
    l.appendChild(t); l.appendChild(i);
    l.remettre = function () { i.value = etat[cle]; dire(); };
    return l;
  }

  var barre = document.createElement('div');
  barre.className = 'reglages-3d';

  var c1 = curseur('Lumière', 'expo', 0.4, 2.2, 0.05);
  var c2 = curseur('Ombre portée', 'ombre', 0, 2, 0.05);
  barre.appendChild(c1);
  barre.appendChild(c2);

  var l3 = document.createElement('label');
  l3.className = 'reglage bascule';
  var b3 = document.createElement('input');
  b3.type = 'checkbox'; b3.checked = etat.tourne;
  b3.addEventListener('change', function () {
    etat.tourne = b3.checked; appliquer(); ecrire();
  });
  l3.appendChild(b3);
  l3.appendChild(document.createTextNode(' rotation automatique'));
  barre.appendChild(l3);

  var raz = document.createElement('button');
  raz.type = 'button'; raz.className = 'plein-ecran';
  raz.textContent = 'valeurs d’origine';
  raz.addEventListener('click', function () {
    etat.expo = DEFAUTS.expo; etat.ombre = DEFAUTS.ombre;
    etat.tourne = DEFAUTS.tourne && !reduit;
    b3.checked = etat.tourne; c1.remettre(); c2.remettre();
    appliquer(); ecrire();
  });
  barre.appendChild(raz);

  var grille = document.querySelector('.cartes-3d');
  grille.parentNode.insertBefore(barre, grille);
  appliquer();
})();
