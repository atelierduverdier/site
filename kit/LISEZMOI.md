# Le kit — charte commune de l'Atelier du Verdier

Ce dossier est **la source unique** de l'identité visuelle des sites de l'Atelier du
Verdier. Il sera recopié dans chaque site satellite par `outils/diffuser_kit.py`
(chantier 3, pas encore écrit).

## La règle, une seule

**On édite le kit ICI, jamais dans une copie.** Une copie sera écrasée au prochain envoi,
sans prévenir. Chaque fichier porte un bandeau qui le rappelle.

C'est la même précaution que la ligne `VERSION` de LaserAtelier, restée 44 versions en
retard parce qu'elle était recopiée à la main dans six fichiers. Ici la divergence a déjà
commencé : le site laser et le journal PrintNC n'ont plus la même charte.

## Contenu

| Fichier | Rôle |
|---|---|
| `verdier.css` | Jetons de couleur (clair + sombre), base typographique, composants partagés |
| `verdier.js` | Bascule de thème, menu en étroit, visionneuse d'images, **entrée des blocs dans le champ**. Défensif : ne plante pas sur une page qui n'a rien de tout ça |
| `verdier-jetons.css` | **Engendré** par `extraire_jetons.py` : les seuls jetons, pour un satellite qui garde sa mise en page |
| `verdier-entete.css` | **Engendré** par `extraire_entete.py` : la barre du haut seule, pour les mêmes |
| `verdier-mouvement.css` | **Engendré** par `extraire_mouvement.py` : la part portable du mouvement (section 13bis-a), pour les mêmes |
| `entete.html` | Du `<!DOCTYPE>` à `</header>` : méta, anti-clignotement, barre du haut |
| `pied.html` | Pied de page, visionneuse, scripts, `</body></html>` |
| `chapeau.svg` | La marque seule, copiée **verbatim** depuis `graphtec-ce6000/resources/icons/` |
| `faire_logo.py` | **Engendre** les deux fichiers ci-dessous. Le logo ne se dessine pas à la main |
| `logo.svg` | Chapeau + « Atelier du Verdier », **autonome** : couleurs figées + `@media` pour le thème sombre. Pour l'extérieur (GitHub, Ko-fi, carte de visite) |
| `logo-inline.svg` | Le même, mot-symbole en `currentColor` : c'est celui que le générateur **colle** dans les pages, pour qu'il suive le bouton de thème |

### Le logo

`python3 kit/faire_logo.py --apercu` régénère les deux variantes et deux PNG de contrôle.

Trois choses valent d'être sues avant d'y toucher :

- **Le texte est converti en courbes.** Un logo qui dépend d'une police installée change
  d'aspect d'une machine à l'autre, et disparaît sur un poste qui ne l'a pas. Inkscape fait
  la conversion une fois, à la génération.
- **La police est Fira Sans**, sous licence SIL Open Font License — libre d'emploi, y
  compris commercial. Les polices de `~/Projets/archives/Fonts` sont écartées **volontairement** :
  plusieurs sont marquées *PERSONAL USE ONLY*, ce qui exclut un logo d'atelier.
- **Les identifiants Inkscape du chapeau sont retirés** à la composition. Le logo est collé
  deux fois par page (barre du haut et pied) et des `id` dupliqués rendent le document
  invalide. Vérifié avant de les enlever : rien ne les référence.

### Les marques des gabarits

`entete.html` : `{{TITRE}}` `{{DESCRIPTION}}` `{{RACINE}}` `{{SOUS_TITRE}}` `{{NAV}}` `{{LOCAL_CSS}}`
`pied.html` : `{{RACINE}}` `{{SOUS_TITRE}}` `{{RESUME}}` `{{LIENS}}` `{{ANNEE}}` `{{LOCAL_JS}}`

`{{RACINE}}` est le chemin vers ce dossier depuis la page produite (`""`, `"../kit/"`…).
Un générateur qui oublie une marque doit **s'arrêter**, pas produire la page : voir
`essai/construire_essai.py`, qui refuse de laisser passer un `{{TROU}}`.

## Ce que le kit ne contient pas, volontairement

Les composants propres à un seul site restent dans une feuille locale, chargée **après**
celle du kit :

- site laser : cartes de mode (`.mode`), schémas (`.diagram`), `details.howto`, la plaque
  blanche sous le logo du héros ;
- journal PrintNC : les quatre couleurs de phase (méca, élec, LinuxCNC, laser).

Le kit sert à arrêter la divergence, pas à tout uniformiser.

## Le mouvement, et pourquoi il est coupé en deux

La section **13bis** de `verdier.css` donne au site son temps : les blocs montent
doucement en entrant dans le champ, les cartes se soulèvent, le héros porte un halo.
Elle est coupée en deux parts, et cette coupure est ce qui permet d'en donner un
morceau aux satellites :

- **13bis-a, portable** — ne nomme que ce que le kit écrit lui-même (`.js-reveal`,
  posé par `verdier.js`). Aucune collision possible avec la feuille d'un hôte.
  `extraire_mouvement.py` en tire `verdier-mouvement.css`.
- **13bis-b, maison** — s'appuie sur `.carte`, `.hero`, `.btn`. Reste au portail et
  au site laser, qui chargent `verdier.css` en entier. La donner à un site qui a sa
  propre mise en page, c'est rejouer les **258 px** du 12/08/2026.

Deux garde-fous mordent dans `extraire_mouvement.py` : les bornes de la section, et
une liste de classes **interdites** dans la part portable. Vérifiés par sabotage.

### Un satellite qui veut le mouvement sur SES blocs

Le kit ne connaît que ses propres noms de classes. Un hôte se déclare :

```html
<meta name="verdier-mouvement" content=".doc-section, .recit-p">
```

Ce qu'il déclare **s'ajoute** à la liste du kit.

### Une page qui construit sa vue après le chargement

`verdier.js` balaie une fois, au chargement. Le journal PrintNC, lui, garde ses 112
blocs de récit derrière quatre cartes : au balayage, **aucun n'est rendu**. Il rappelle
donc le kit quand la vue existe :

```js
window.verdierMouvement.rescanner(element)
```

**Là où il ne faut pas l'appeler : sur un filtre ou une recherche.** Faire apparaître
en fondu des résultats que le visiteur vient de demander, c'est le faire attendre pour
ce qu'il a déjà demandé.

### Le décalage se calcule à l'entrée, pas au marquage

Le ruissellement d'une rangée de cartes vient du fait qu'elles **entrent ensemble** —
pas du fait d'être voisines dans le balisage. L'observateur livre justement par paquets :
ce qui a franchi la ligne dans la même image. Chaque paquet est trié de haut en bas, et
le retard est l'indice dans le paquet (60 ms, plafonné à 5).

La première version prenait le rang parmi les **frères**. Mesuré sur le récit du journal
PrintNC — quarante paragraphes tous frères, rangs `[0,1,2,3,4,5,5,5,5,5]` : à partir du
sixième, chaque paragraphe traînait **300 ms** de retard sur le moment juste. Un
paragraphe qu'on atteint en lisant doit paraître maintenant.

### Pas de bloc marqué dans un bloc candidat

Deux raisons, et la seconde mord fort. La visible : une carte qui monte pendant que sa
rangée de liens monte à son tour, ce sont deux mouvements pour une seule chose.

L'autre : `.js-reveal` pose un `transform`, et **un élément transformé devient le bloc
conteneur** de ses descendants positionnés en absolu. Le recouvrement qui rend la carte
cliquable se repliait alors sur la seule rangée de liens — 319 × 74 au lieu de
365 × 376. Le test porte sur les **candidats**, pas sur les marqués : les premières
cartes d'une page sont au-dessus du pli, donc écartées, mais leur rangée de liens tombe
dessous et se ferait marquer.

## La carte entière emmène au lien — et seul ce qui mène quelque part bouge

Une carte qui se soulève au survol annonce qu'on peut cliquer dessus : elle doit l'être.
`verdier.js` **désigne** le premier lien de chaque `.carte` ou `.panel` (`carte-cible`) et
pousse les suivants au-dessus (`carte-dessus`) ; la feuille étire le `::after` du premier
sur tout le bloc.

**Le soulèvement suit `.carte-cliquable`, pas `.carte`.** C'était `.carte:hover,.panel:hover`,
et ça mentait : sur ce site, **21 des 25 panneaux n'ont aucun lien** et se soulevaient
quand même. Un bloc qui bouge sous le curseur annonce un clic ; s'il n'en a pas, il ment.
Un bloc déjà cliquable de lui-même (`<a>`, `<button>`, `[onclick]` — les quatre cartes
d'accueil du journal PrintNC) est marqué lui aussi, sans recouvrement : il mène bien
quelque part, il a droit à sa réponse au survol.

Un vrai lien, pas un gestionnaire de clic : le clic du milieu, « ouvrir dans un nouvel
onglet », l'adresse dans la barre d'état et la tabulation continuent de marcher. Les
autres liens de la carte — documentation, manuel, dépôt — gardent leur clic propre.

Ce que ça coûte : **on ne peut plus sélectionner le texte de la carte à la souris**.
C'est le prix connu de ce motif.

Ne sont pas touchées : une carte qui est déjà un `<a>` ou un `<button>` (le journal
PrintNC fait ses quatre cartes d'accueil en boutons), et une carte sans lien.

## Le soulignement se tire

`a:hover{text-decoration:underline}` allumait un trait d'un coup. Il se dessine
maintenant de gauche à droite — un dégradé en fond, parce que `text-decoration` ne
s'interpole pas. Le trait prend `currentColor`, donc il suit le lien sur les deux thèmes
sans qu'on ait à le redire.

Boutons, marque et onglets de navigation en sont exclus : ils ont déjà leur réponse au
survol. Et sous `prefers-reduced-motion`, le trait franc **revient** — ce qu'on retire,
c'est le mouvement, pas l'information.

### Les deux règles qui protègent le contenu

Ce dispositif n'a qu'un mauvais dénouement possible : un bloc marqué `opacity:0` que
rien ne révèle — du **contenu invisible, sans message**. Deux choses l'empêchent :

1. **Un bloc non rendu n'est jamais marqué.** Un élément derrière un filtre
   (`display:none`) mesure 0 : il est écarté. Sinon, le jour où le filtre le rouvre,
   il serait invisible pour toujours.
2. **Le filet.** Si l'observateur ne tire pas — onglet d'arrière-plan, retour de
   bfcache, navigateur qui throttle — un passage retardé montre ce qui est dans le
   champ. Mesuré le 27/08/2026 dans un onglet non affiché : Chrome cesse de délivrer
   les intersections, onze blocs restaient à zéro. Le filet se retire dès qu'il n'y
   a plus rien à couvrir.

## Le chapeau

**Noir, avec un liseré blanc.** Le liseré est ce qui le détache d'un fond sombre — il ne
faut pas le repeindre en blanc pour le faire ressortir : ce n'est plus le logo.
`paint-order: stroke fill` met le liseré derrière le remplissage ; sans ça il mange la
silhouette de moitié.

Le SVG est la version **sans résidus Inkscape**. Les attributs `inkscape:*` privés de leur
namespace invalident le fichier, et QtSvg ne rend alors rien — silencieusement. Valider
toute retouche avec `xmllint --noout kit/chapeau.svg`.

## Décisions techniques, et pourquoi

**Le thème est rangé dans un cookie, pas dans `localStorage`.** `localStorage` est
cloisonné par origine : un réglage fait sur `atelierduverdier.fr` ne suivrait pas le
visiteur sur `laser.atelierduverdier.fr`. Le cookie est posé sur le domaine parent. Pas de
bandeau de consentement à prévoir : mémoriser un choix d'affichage exprimé par le visiteur
lui-même est dispensé de consentement, et GoatCounter ne pose aucun cookie.

**La balise `<html>` ne porte pas de `data-theme` en dur.** Le site laser écrit
`data-theme="light"` : comme `:root[data-theme="light"]` est plus spécifique que le bloc
`@media (prefers-color-scheme: dark)`, un visiteur dont le système est en sombre reçoit la
page blanche. Vérifié au navigateur le 11/08/2026 — fond rendu `rgb(255,255,255)` système
en sombre, alors que le thème sombre du site existe bel et bien (`#14171b`) et n'est
atteignable que par le bouton ◐.

**L'anti-clignotement est en ligne dans le `<head>`.** `verdier.js` est chargé en fin de
page : sans ce petit script, un visiteur ayant choisi le thème sombre verrait la page
claire une fraction de seconde à chaque chargement.

**`.twrap` est obligatoire autour de chaque `<table>`.** Sans lui, un tableau large fait
défiler la page entière de travers sur téléphone. Vérifié : avec, le tableau défile dans
son propre cadre et la page reste droite.

## Limite connue, à traiter au chantier 1

**Il n'y a pas de navigation sur téléphone.** Sous 860 px, `.navlinks` passe en
`display:none` et rien ne la remplace — pas de menu déroulant. C'est hérité du site laser.
Acceptable pour une page unique à ancres, insuffisant pour un portail multi-pages.

## Vérifier le kit

```bash
python3 essai/construire_essai.py
```

Puis ouvrir `essai/index.html`. La page d'essai montre tous les composants sur du contenu
réel — une charte se juge à l'écran, pas dans un fichier.
