# Plan — site général « Atelier du Verdier »

Cadrage du 11/08/2026. **Les six décisions structurantes sont prises** (§6) ; les chantiers
du §5 peuvent démarrer dans l'ordre. Le contenu rédactionnel reste entièrement à écrire.

---

## 1. Ce qui existe déjà (inventaire vérifié, pas de mémoire)

### Sites en ligne — il y en a **trois**, pas deux

| Domaine | Sert quoi | Dépôt | Comment c'est fait |
|---|---|---|---|
| `atelierduverdier.fr` | Journal de construction PrintNC (277 vidéos) | `printnc-build` (public) | `generer_site.py` → **un seul `index.html` de 588 Ko** depuis `data/videos.csv` |
| `laser.atelierduverdier.fr` | LaserAtelier : présentation + manuel + PDF | `LaserAtelier/docs/` (public) | HTML écrit à la main, 11 sections, `manuel.html` de 352 Ko |
| `liens.atelierduverdier.fr` | Page « Mes liens » | `liens` (public) | Page unique |

Tout est hébergé sur GitHub Pages. GoatCounter est déjà branché sur le journal PrintNC
(y compris un événement personnalisé `/vote-utile`).

### Logiciels

| Logiciel | Dépôt | Visibilité | État |
|---|---|---|---|
| LaserAtelier (workbench FreeCAD) | `LaserAtelier` | **public** | v2.99.15, cap sur une v3 stable |
| Config LinuxCNC PrintNC + changeur d'outil | `printnc-config` | **public** | changeur poussé le 09/08/2026 |
| Visualiseur G-code LinuxCNC | `visualiseur-gcode` | **privé** | v1 le 10/08/2026 |
| Pupitre Graphtec CE6000-60 | `graphtec-ce6000` | **privé** | fini le 11/08/2026 |

Satellites publics qui existent aussi : `gsr-gui` (enregistreur d'écran, hors atelier),
`huanyang-vfd-reader` (lecture VFD, atelier-adjacent).
Non publiés : AMAP-Crouay, `atelier-telegram-bot`, les projets FreeCAD (magasin ATC,
dust shoe, meuble à balais, tonnelle).

### Identité

Le chapeau melon existe (`chapeau.svg`, signature déjà présente dans chaque icône de mode
LaserAtelier). Mais **les deux sites ont déjà divergé** :

- laser : orange `#ff8a00` sur ardoise `#2f3540` — c'est la charte du chapeau ;
- journal PrintNC : fond `#13110e`, palette par phase (bleu `#378ADD`, orange `#EF9F27`,
  vert `#1D9E75`, rouge `#C44A31`).

Deux chartes après deux sites. Au quatrième, ce sera ingérable.

---

## 2. Le vrai problème structurel

**La racine du domaine est déjà occupée par le journal PrintNC.**

Un site général veut cette racine — c'est l'adresse qu'on donne à l'oral, celle qui est sur
la carte de visite. Or `atelierduverdier.fr` sert aujourd'hui un journal de construction, et
les liens partagés ailleurs (Instagram, forum PrintNC) pointent dessus **avec des ancres**
(`atelierduverdier.fr/#video-…`). GitHub Pages ne sait pas faire de redirection 301 côté
serveur, et une ancre n'est de toute façon jamais envoyée au serveur.

C'est le seul point de ce plan qui peut casser quelque chose de visible. Il est traité au
chantier 2.

Second problème, moins urgent mais déjà là : le journal est **une seule page de 588 Ko** pour
277 vidéos, plus 632 miniatures (dépôt de 42 Mo). Le générateur monopage a atteint sa limite.

---

## 3. Statique ou dynamique

### ✅ Décidé : **statique, généré par un script Python maison.**

Le critère n'est pas « statique c'est plus simple », c'est : *qui écrit les données ?*
Ici, **seul toi**. Pas de compte utilisateur, pas de commentaire, pas de panier, pas de
formulaire. Un site dynamique se justifie quand un visiteur écrit dans la base. Aucun visiteur
n'écrira ici.

Ce qui plaide concrètement pour le statique dans **ton** cas précis :

1. **C'est déjà ce que tu fais.** `generer_site.py` lit un CSV et crache du HTML ; le manuel
   LaserAtelier est généré en PDF par WeasyPrint ; l'AMAP a aussi son `generer_site.py`. Le
   flux « données → script Python → HTML » t'est familier, il est versionné, il se rejoue.
2. **Zéro maintenance de sécurité.** Un site dynamique, c'est un VPS, un runtime à tenir à
   jour, des sauvegardes, une surface d'attaque — pour des pages qui ne changent que quand
   *tu* changes un fichier.
3. **Zéro coût.** GitHub Pages est gratuit et déjà en place sur les trois sites.
4. **Versionné avec le code.** Le manuel LaserAtelier vit dans `docs/` du même dépôt que le
   workbench : c'est exactement ce qui garantit que la doc suive la `VERSION`. Un CMS séparé
   casserait ce lien.
5. **Ça marche hors ligne** dans l'atelier, et ça s'archive.

### Ce qu'on croit avoir besoin de dynamique, et qui n'en a pas besoin

| Envie | Solution statique |
|---|---|
| Recherche dans la doc | index JSON + recherche en JS côté client |
| Filtrer les vidéos par phase/mois | déjà fait aujourd'hui, en JS |
| Compteur de vues, stats | GoatCounter — **déjà branché** |
| Flux RSS | fichier généré |
| Dernière version d'un logiciel | lue à la génération depuis `VERSION` / l'API GitHub, figée dans la page |

### Ce qui ferait rouvrir la question

Un seul de ces trois suffirait : **commentaires**, **formulaire de contact avec pièce jointe**,
ou **vente** (plans, pièces usinées). Aucun n'est prévu au 11/08/2026 — c'est ce qui rend la
décision facile. Si l'un des trois revient plus tard, la réponse restera probablement « site
statique + service tiers » (formulaire hébergé, boutique externe) plutôt qu'un serveur à toi :
le statique n'est pas une impasse.

---

## 4. Architecture proposée

### Le modèle : **fédération, pas fusion**

Un dépôt `site` nouveau qui porte **la racine + les fiches logiciels + la charte commune**.
Chaque projet garde sa doc chez lui, sur son sous-domaine.

```
atelierduverdier.fr            ← NOUVEAU dépôt « site »
├── /                          accueil : le chapeau, qui je suis, les 4 logiciels, l'atelier
├── /logiciels/                les fiches : une par logiciel (capture, à quoi ça sert,
│                              état, lien dépôt, lien doc)
├── /atelier/                  la machine, le laser, le traceur — le matériel
├── /projets/                  les projets d'atelier (magasin ATC, dust shoe, meubles…)
└── /kit/                      LA CHARTE : verdier.css, en-tête, pied de page, chapeau.svg

printnc.atelierduverdier.fr    ← le journal déménage ici (dépôt printnc-build)
laser.atelierduverdier.fr      ← inchangé (LaserAtelier/docs)
gcode.atelierduverdier.fr      ← plus tard : doc du visualiseur
traceur.atelierduverdier.fr    ← plus tard : doc du pupitre Graphtec
liens.atelierduverdier.fr      ← inchangé
```

**Pourquoi fédérer plutôt que tout fusionner dans un dépôt.** Fusionner donnerait une
cohérence parfaite, mais couperait `docs/` de `LaserAtelier` — or c'est précisément cette
cohabitation qui fait que le manuel suit la `VERSION` du workbench, avec le rituel de bump
déjà en place. On ne casse pas ça pour une question de mise en page.

### La charte : un kit copié par script, jamais à la main

C'est le point à ne pas rater. Le dépôt `site` contient `kit/verdier.css` +
`kit/entete.html` + `kit/pied.html` + `chapeau.svg`, et un script
`diffuser_kit.py` les **recopie** dans chaque site satellite (avec une bannière
`<!-- généré depuis atelierduverdier/site, ne pas éditer ici -->`).

Le raisonnement est le même que pour la ligne `VERSION` de LaserAtelier restée 44 versions en
retard, ou pour les chiffres d'effort qu'on recalcule au lieu de les retaper : **une valeur
recopiée à la main dans cinq fichiers finit toujours par diverger.** Ici c'est déjà arrivé,
en deux sites.

Charte de référence : **orange `#ff8a00` sur ardoise `#2f3540`, chapeau noir** — celle du
laser, parce que c'est celle du chapeau. Le journal PrintNC garde ses quatre couleurs de
phase *comme accents de contenu*, mais reprend le fond, la typo, l'en-tête et le pied.

---

## 5. Chantiers, dans l'ordre

Chaque chantier est livrable seul et laisse le site en état de marche.

### Chantier 0 — Fixer la charte ✅ **fait le 11/08/2026**
`kit/verdier.css`, `kit/verdier.js`, les gabarits `entete.html` / `pied.html` et le
`chapeau.svg`, extraits de l'existant du site laser sans retoucher une seule valeur de
jeton. Page d'essai dans `essai/`, assemblée **par les gabarits** (`construire_essai.py`)
pour les valider en même temps que la charte. Contrat du kit dans `kit/LISEZMOI.md`.
Rien en ligne, aucun site existant touché.

Trouvé en chemin, corrigé dans les gabarits : le site laser écrit `data-theme="light"`
en dur, ce qui neutralise `prefers-color-scheme` — un visiteur en thème sombre reçoit la
page blanche. Vérifié au navigateur, pas déduit.

Reste ouvert : **pas de navigation sur téléphone** (`.navlinks` en `display:none` sous
860 px, sans menu de remplacement). Hérité du site laser, à traiter au chantier 1.

### Chantier 1 — La page d'accueil ✅ **fait le 12/08/2026**
`site/generer.py` assemble les pages depuis `site/contenu/` et le kit, et écrit tout dans
`site/public/` (entièrement reconstruit à chaque passage). Deux pages :

- **l'accueil** — héros, les 4 fiches logiciels avec leur état, l'atelier, les projets ;
- **`projets/magasin-atc.html`** — la note de calcul de la bille, 7 schémas SVG dessinés
  pour le site + 3 planches TechDraw reprises du projet ATC.

Dette du chantier 0 réglée : **navigation sur téléphone**, panneau déroulant sous 860 px
(`.nav-btn`, refermé au clic, au lien ou par Échap).

Trouvé et corrigé en mesurant : un SVG est étiré à la largeur de sa colonne, donc un même
texte déclaré à 10,5 px se rendait **entre 10,5 et 18,2 px** selon la figure. Les tailles
sont désormais en `em`, chaque figure portant sa base — rendu uniforme à 12 px vérifié.

**La page ATC est branchée sur le modèle** (`site/valeurs_atc.py`) : elle ne contient plus
un seul nombre écrit à la main. Chaque marque est lue dans `note_calcul.valeurs()` du projet
magasin-atc — la fonction même qui engendre la note de calcul en PDF — et le tableau des
saillies est engendré entier. Une clé absente **arrête** la génération.

`magasin_er20` importe FreeCAD, dont l'interpréteur n'existe que si FreeCAD tourne (point de
montage changeant). Deux modules factices suffisent : `valeurs()` ne touche que des constantes
et de la trigonométrie. Le site se régénère donc sans FreeCAD, et **115 grandeurs** sont lues.

**Logo** (12/08/2026) — `kit/faire_logo.py` compose le chapeau et le mot-symbole « Atelier
du Verdier » et engendre deux variantes : une autonome pour l'extérieur, une en ligne que le
générateur colle dans les pages pour qu'elle suive le bouton de thème. Texte converti en
courbes (Fira Sans, licence OFL). Il remplace le chapeau seul dans la barre du haut, le pied
et le héros de l'accueil.

**Pages des deux logiciels privés** (12/08/2026) — fiches vitrines sans lien dépôt (choix D3),
faits et chiffres repris des README des projets :

- `logiciels/visualiseur-gcode.html`, six schémas SVG ;
- `logiciels/pupitre-graphtec.html`, cinq schémas SVG.

**Captures du pupitre** (12/08/2026) — `site/outils/capturer_pupitre.py` lance l'application
**hors écran** (`QT_QPA_PLATFORM=offscreen`), lui fait ouvrir un SVG, et grabbe ses trois
onglets. Il **refuse de démarrer si le traceur est branché** : aucune image ne vaut le risque
de faire bouger une plume sur du papier.

**Ordre de la page du pupitre repris** à la demande de Christophe : le mode d'emploi et les
captures d'abord, l'archéologie du protocole ensuite et **repliée** dans des
`details.pliable`. Une page qui s'ouvre sur du protocole propriétaire décourage avant d'avoir
dit à quoi sert le programme. Le détail n'est pas retiré, il est derrière un panneau.

**Captures du visualiseur** (12/08/2026) — `site/outils/capturer_visualiseur.py` appelle
l'outil du projet lui-même (`outils/capturer.py`), qui compose l'habillage Qt et le tampon
OpenGL : un `grab()` ordinaire ne traverse pas la vue 3D. Quatre images — le fichier
paramétré d'origine, la gravure colorée par profondeur, le bloc de bois à mi-parcours, et le
bandeau d'erreur sur `site/exemples/arc_fautif.ngc`, une fixture écrite exprès.

`rs274` est nécessaire : il tourne par le lanceur `~/.local/bin/rs274` qui passe par
distrobox. `capturer.py` écrit son PNG **puis meurt en core dump** au démontage OpenGL hors
écran — sans effet sur l'image ; le pilote juge donc sur l'existence et la fraîcheur du
fichier, pas sur le code de retour.

Une modification faite **dans le projet visualiseur** : `outils/capturer.py` orientait la
caméra sans cocher le bouton de vue, si bien qu'une capture `--vue iso` montrait « Dessus »
en surbrillance — un état que l'application n'atteint jamais. Neuf lignes ajoutées.

**Page du visualiseur réordonnée** comme celle du pupitre : captures et usage d'abord,
architecture et pièges repliés. Repliée elle fait 6 527 px, tout ouvert 10 065.

**Page LaserAtelier** (12/08/2026) — `logiciels/laseratelier.html`. C'est le seul logiciel qui
avait **déjà** son site complet, d'où un périmètre choisi : cette page raconte ce que la doc ne
raconte pas — pourquoi l'atelier existe, la contrainte matérielle qui commande toute la
génération du G-code (à l'arrêt la puissance tombe à zéro), et la discipline de mesure sur bois.
Pour le comment-faire, elle renvoie à `laser.atelierduverdier.fr`. Trois schémas SVG, trois
captures reprises du dépôt LaserAtelier et réduites par `site/outils/reprendre_captures_laser.py`.

La **version est lue dans `laser_core.py`** à chaque génération (`{{laser.version}}`), sur
l'accueil comme sur la page — elle y était écrite en dur, exactement le piège de la ligne
VERSION. Le chiffre « ≈ N heures » du site laser n'est **volontairement pas repris** : il est
recalculé par `outils/chiffrer_effort.py` et vit déjà dans trois fichiers.

Le chantier 4 est **fait** : les quatre logiciels ont leur page.

**Captures en WebP** (12/08/2026) — `generer.py` convertit les PNG de `contenu/captures/` au
moment de publier ; les PNG restent les maîtres. **Le mode est mesuré, pas supposé** : sur une
interface à aplats le WebP sans perte bat le lossy de moitié (77 Ko contre 153 à q92), sur une
capture à dégradés c'est l'inverse (350 contre 96). On encode donc les deux et on garde le plus
petit — les 13 captures ont toutes choisi le sans perte.

**1 852 Ko → 652 Ko, 65 % de moins.** Le site passe de 3,3 Mo à **1,44 Mo**.

**Captures LaserAtelier refaites** (12/08/2026) — celles du site venaient de
`docs/screenshots/*.png`, quatre captures plein écran **du 16 juillet** que le script du dépôt ne
régénère pas. Entre-temps les panneaux ont beaucoup grossi. La source est maintenant
`docs/manuel_img/`, recadrée pour un document, et six panneaux sont montrés en grille à leur
largeur juste de 430 px — les étirer les rendrait flous.

Côté dépôt LaserAtelier (commit `737d415`, poussé) : `tests/captures.py` ne connaissait que 20
panneaux sur 22 — Calligraphie et Texte contour avaient été faits à la main et sortaient à 453 px
au lieu de 430. Les 22 sont régénérés, le PDF du manuel aussi (98 pages). **Config vivante
vérifiée intacte** avant et après, md5 et mtime identiques.

Le paragraphe « qui je suis » a été écrit le 12/08/2026 (nom, oiseau, Normandie, le bois
et le code jugés sur une pièce), puis **retiré le jour même à la demande de Christophe**.
Le texte reste dans l'historique git (commit `dbf450a`) pour le jour où il le remettra.

Le dossier est un **dépôt git local** depuis le 12/08/2026. **Rien n'est en ligne** —
pas de dépôt GitHub, pas de DNS.

### Chantier 2 — La bascule de la racine ⚠️ — filet ÉCRIT et ÉPROUVÉ le 12/08/2026

**La grammaire supposée par ce plan était fausse.** Les ancres du journal ne sont pas
`#video-…`/`#mois-…` mais, relevées dans `initFromHash` de son `generer_site.py` puis
comptées sur le site EN LIGNE : `#v-…` (266), `#doc-…` (17), `#gloss-…` (8), les onglets
`#all #doc #gloss #maj #recit`, et les mois `#AAAA-MM`. Tester sur du réel n'était pas un
luxe : le filet imaginé par ce plan n'aurait rien rattrapé du tout.

**Le filet** vit en tête du corps de l'accueil (`site/contenu/accueil.html`), en
`location.replace` (pas d'entrée d'historique). Les ancres propres au portail
(`#logiciels #atelier #projets #qui`…) ne matchent aucun motif du journal et restent.

**Éprouvé au navigateur le 12/08/2026 :**
- flux réel — la page chargée avec une vraie ancre `v-` tente immédiatement de partir vers
  `printnc.atelierduverdier.fr/#même-ancre` (visible dans les journaux du serveur : la page
  est servie puis le navigateur ressort) ; sans ancre, ou avec `#logiciels`, elle reste ;
- grammaire déployée — extraite de la page PRODUITE et rejouée sur **18 cas** : 9 ancres
  réelles du site en ligne partent avec l'ancre préservée, 9 ancres du portail restent.
  Zéro erreur.

**12/08/2026, sur « fais-le » de Christophe — le portail est EN LIGNE sous l'URL GitHub :**
<https://atelierduverdier.github.io/site/> — dépôt public `atelierduverdier/site`, source sur
`main`, produit poussé sur `gh-pages` par `site/publier.py` (un commit unique, force-poussé,
estampillé du commit de `main` qui l'a engendré). La page servie est **md5-identique** à celle
éprouvée au navigateur : les tests du filet valent pour la production. CSS, page ATC et
captures WebP répondent 200.

**L'ORDRE DE FIN DE BASCULE A CHANGÉ — le DNS passe AVANT les CNAME.** L'ordre initial de ce
plan (CNAME puis DNS) aurait laissé le journal HORS LIGNE entre les deux : dès que
`printnc-build` lâche la racine, le journal n'est joignable qu'à `printnc.…`, qui ne résout
pas encore. Relevé au `dig` le 12/08/2026 : l'apex et `www`/`laser`/`liens` pointent bien vers
GitHub Pages, **`printnc` n'existe pas, pas de wildcard**.

### ✅ **BASCULÉ le 12/08/2026.** `atelierduverdier.fr` sert le portail.

Ordre suivi, et il compte : **DNS chez OVH d'abord** (Christophe), puis le journal libère la
racine, puis le portail la réclame. L'ordre inverse aurait laissé le journal hors ligne entre
les deux.

| domaine | sert | vérifié |
|---|---|---|
| `atelierduverdier.fr` | le portail | 200, certificat valide |
| `www.` | le portail | 200 |
| `printnc.` | le journal | 200, **md5 identique à avant la bascule** |
| `laser.` · `liens.` | inchangés | 200 |

**Le filet à ancres, éprouvé trois fois plutôt qu'une :**

1. *Sur les 317 ancres réelles du journal*, avec le code JS **extrait de la page servie** et
   rejoué sous node : **294 rattrapées**. Les 23 restantes (`#theme-toggle`, `#lightbox`,
   `#search-input`…) ne sont **jamais des cibles de lien** — que des `id` de widgets, vérifié
   contre la liste des `href="#…"` du journal. Zéro fuite : les quatre ancres propres au
   portail restent sur place.
2. *En vrai navigateur* (Firefox headless, JS actif), sur trois vraies ancres relevées en
   ligne : **3/3 aboutissent sur l'élément visé, à l'écran** — position mesurée, pas déduite.
3. *Comparé au direct* : mêmes ancres sans passer par le filet, mêmes positions (top=113).

**Un faux défaut, à ne pas rechercher** : un premier passage donnait 2/3, l'ancre `#v-18088…`
trouvée mais à 1697 px hors écran. C'était **le temps d'attente du test**, pas le filet — la
redirection ajoute un chargement de page. À 9 s de repos : 3/3, trois passages de suite, à la
position exacte du cas direct.

**Défaut réel trouvé après bascule, corrigé** : le pied du portail et la fiche « Journal de
construction » pointaient encore `atelierduverdier.fr`, devenu le portail lui-même — un lien
qui tourne en rond. Redressés vers `printnc.`. Le journal, lui, n'avait aucun lien absolu vers
lui-même : rien à y changer.

**GoatCounter — réglé le 12/08/2026, sans rien demander de plus.** Christophe a dit ne pas
regarder ces statistiques et ne pas les trouver intuitives ; il n'y avait donc pas de décision
à lui rendre, seulement le choix le moins cher et le moins irréversible.

Le problème était réel : `count.js` envoie `p` (chemin), `r`, `t`, `e`, `s`, `b`, `q` — **le
nom d'hôte n'en fait pas partie**, vérifié dans le script lui-même. Le `/` du portail et celui
du journal tombaient donc dans le même seau depuis la bascule du matin.

**C'est le nouveau venu qui se préfixe** (`/portail…`), jamais le journal : lui a des mois
d'historique sur `/`, et le couper en deux séries perdrait la continuité qu'on cherche à
préserver. Vérifié en navigateur sur les pages produites : `/` devient `/portail/`,
`/logiciels/laseratelier.html` devient `/portail/logiciels/…`. Journal inchangé, md5 identique.

Le préfixe est un **réglage du générateur** (`PREFIXE_COMPTEUR`), pas une ligne écrite dans le
kit : un futur satellite seul sur son compte mettra `''`. L'événement `/vote-utile` du journal
porte un chemin explicite et n'est pas concerné.

Si un jour Christophe veut vraiment lire ces chiffres, la question à reposer n'est pas le
préfixe mais l'outil.

### Chantier 3 — Diffuser la charte
**`diffuser_kit.py` : fait le 12/08/2026. Site laser : fait. Journal PrintNC : à faire.**

Le script pose `verdier.css`, `verdier.js`, `verdier-chapeau.svg` et `verdier-logo.svg` chez
chaque satellite, avec un bandeau d'origine et une empreinte par fichier. Trois garde-fous,
tous **éprouvés** : une copie retouchée sur place arrête la diffusion (`--forcer` l'écrase) ;
un fichier existant jamais posé par le kit n'est pas écrasé ; deux passages ne réécrivent rien.

Les noms posés sont préfixés `verdier-*`, et ça vient d'une vraie casse : la première version
a écrasé `docs/assets/logo.svg` du site laser — 40 Ko, utilisés dans son héros — par simple
collision de nom. Restauré depuis git, puis les **deux** causes corrigées : le nom, et
l'absence de refus.

**Le script ne touche aucun HTML.** Brancher une page sur la charte se fait une fois, à la
main, avec les yeux dessus ; ensuite les fichiers restent synchronisés tout seuls.

#### Site laser — branché, et vérifié plutôt que supposé

Les 14 Ko de `<style>` en ligne cèdent la place à `assets/verdier.css` (la charte) et
`assets/laser-local.css` (3 Ko, les 33 blocs propres au site : cartes de mode, schémas,
dépliants, plaque du héros). Sur 53 sélecteurs relevés, **52 ont des styles calculés
identiques** avant/après, et la page fait exactement la même hauteur : 25 221 px. Le 53ᵉ est
`.pipe`, dont la grille `auto-fit` ajoute une piste de 0 px dans la valeur calculée — mesuré
sans effet : mêmes six colonnes, mêmes positions, même largeur.

Deux défauts corrigés au passage, tous deux mesurés en ligne :

- `data-theme="light"` en dur neutralisait `prefers-color-scheme`. Navigateur en thème
  sombre : fond `rgb(255,255,255)` avant, `rgb(20,23,27)` après.
- aucune navigation sous 860 px. Le bouton de menu de la charte est en place, éprouvé à
  390 px.

Le thème passe de `localStorage` à un **cookie de domaine** : le réglage suit le visiteur
d'un sous-domaine à l'autre. Contrepartie, une fois : un choix déjà enregistré est oublié.

`manuel.html` n'est **pas** touché — il part en PDF par WeasyPrint et garde son style en ligne.

#### Journal PrintNC — fait le 12/08/2026, variante « ardoise »

Deux variantes ont été préparées et montrées avant de trancher : garder l'identité chaude, ou
adopter l'ardoise commune. **La mesure a éliminé la première** — sur 22 sélecteurs, une seule
marge changeait : le journal définit ses 209 règles lui-même, la charte n'avait rien à lui
servir. Le choix réel était donc binaire, et Christophe a pris l'ardoise.

**Le journal ne charge que les JETONS, pas la charte entière**, et c'est une mesure qui l'a
imposé. Avec `verdier.css` complet : titre du héros à **43,2 px au lieu de 30**, paragraphes
avec 12,6 px de marge — la cause est la spécificité, `.hero h1` du kit bat `.hero-titre` du
journal. Dix-sept sélecteurs se croisent, et la spécificité en crée d'autres qui ne se voient
pas au nom. Avec `kit/verdier-jetons.css` : titre 30 px, marges 0, **page 1620 px des deux
côtés**. Identique.

`kit/extraire_jetons.py` tire ce fichier de `verdier.css` — jamais écrit à la main, pour que
les deux ne divergent pas. `diffuser_kit.py` sait désormais poser **des jeux différents selon
le satellite** : la charte entière au site laser, les jetons seuls au journal.

Thème unifié : `data-theme` + cookie de domaine, la logique venant de `verdier.js`. Le réglage
traverse donc les sous-domaines. `body.jour` et son `localStorage` disparaissent ; il ne reste
localement que l'icône soleil/lune. Les **quatre couleurs de phase sont intactes**.

**Un piège de mesure, à ne pas refaire.** Les premiers relevés annonçaient +141, +258 puis
+83 px de croissance. Tous faux : mon témoin était un bac à sable contenant `generer_site.py`
et `data/` **mais pas les images**. L'image du héros ne s'affichant pas, le texte prenait
toute la largeur au lieu de partager avec elle — la page paraissait plus courte. Comparé au
vrai dossier, images comprises : 1620 px contre 1620. Un témoin doit être le vrai site, pas
une reconstitution.

Le chantier 3 est **fait**.

### Chantier 4 — Les deux logiciels privés (½ journée)
**Fiche vitrine, sans lien dépôt** (choix D3) : captures + ce que ça fait + état, pour
`visualiseur-gcode` et `graphtec-ce6000`. Réversible : le jour où l'un passe en public, on
ajoute le lien, rien d'autre à refaire.

Si ce jour arrive, la relecture préalable n'est pas une formalité — secrets, chemins
personnels, `config.env`, adresses. Une fois poussé, c'est public pour toujours.

### Chantier 5 — Découper le journal PrintNC : **mesuré le 12/08/2026, PAS FAIT, et à raison**

Le plan disait « à faire quand ça gênera vraiment ». Mesuré : **ça ne gêne pas**.

| grandeur | relevé sur le site en ligne |
|---|---|
| poids transféré | **103 Ko** compressés (598 Ko en clair — gzip fait le travail) |
| DOM interactif | **231 ms** |
| chargement complet | **236 ms** |
| images réellement tirées | **2** sur 299 (296 en chargement paresseux) |
| bascule d'un onglet | **1 ms** |

Le « 588 Ko » du cadrage était le poids sur disque, jamais celui sur le fil.

**Et le découpage casserait trois choses qui marchent aujourd'hui :**

1. **Toutes les ancres partagées.** Les `#v-…` valent parce que les 265 vidéos sont dans un
   seul document. Réparties par mois, chaque lien Instagram ou forum demanderait un second
   filet — celui du chantier 2 mène à la racine du journal, pas à la bonne page mensuelle.
2. **La recherche.** Elle filtre les `.item` du document courant : découpée, elle ne verrait
   plus que le mois affiché. Rendre la recherche globale demanderait un index séparé.
3. **Le filtre par phase**, pour la même raison.

**Le seuil, calculé sur le coût unitaire mesuré** — 0,39 Ko compressés, 26 nœuds et 0,87 ms
par vidéo, à un rythme relevé de 39,7 vidéos par mois :

- 300 Ko compressés vers **772 vidéos**, soit ~13 mois (≈ 08/2027) ;
- 1 s d'interactivité vers **1 147 vidéos**, soit ~22 mois (≈ 06/2028).

**Le déclencheur à surveiller n'est donc pas une date, c'est un compteur : ~770 vidéos.**
D'ici là, découper coûterait trois régressions certaines pour un gain nul.

### Chantier 6 — La rubrique `/projets/` (plus tard)
Magasin ATC, dust shoe, meuble à balais, tonnelle, AMAP. Prévue dans l'architecture dès
maintenant pour ne pas avoir à la greffer, remplie **après** la mise en ligne du portail
(choix D6) : c'est du contenu à écrire, ça ne doit pas retarder le reste.

---

## 6. Décisions prises — 11/08/2026

| # | Question | Décision |
|---|---|---|
| **D1** | Statique ou dynamique ? | ✅ **Statique, script Python maison** (ni Hugo ni Zola) |
| **D2** | Le portail prend-il la racine ? | ✅ **Oui.** Le journal PrintNC déménage sur `printnc.`, avec le filet à ancres |
| **D3** | `visualiseur-gcode` et `graphtec-ce6000` | ✅ **Fiche vitrine sans lien dépôt.** Ils restent privés |
| **D4** | Sous-domaines ou sous-dossiers ? | ✅ **Sous-domaines** : chaque doc reste dans le dépôt de son logiciel |
| **D5** | Générateur | ✅ **Script maison**, dans la lignée de `generer_site.py` |
| **D6** | Projets non logiciels | ✅ **Oui, rubrique `/projets/`, mais après la mise en ligne** |

Ces six décisions n'engagent rien d'irréversible : la seule opération qui touche du visible
est le chantier 2, et elle est protégée par le filet à ancres et par le passage préalable sur
`nouveau.atelierduverdier.fr`.

---

## 7. Ce que ce plan ne dit pas

- Rien sur le contenu rédactionnel (le « qui je suis », le ton). C'est le plus long à écrire
  et ça ne se planifie pas dans un tableau.
- Rien sur le référencement. À voir une fois qu'il y a quelque chose à référencer.
- Rien sur les langues. Tout reste en français.
