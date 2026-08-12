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
| `verdier.js` | Bascule de thème, menu en étroit, visionneuse d'images. Défensif : ne plante pas sur une page qui n'a rien de tout ça |
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
