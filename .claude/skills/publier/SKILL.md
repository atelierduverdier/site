---
name: publier
description: >-
  Mettre en ligne atelierduverdier.fr : rafraîchir les planches, régénérer, force-pousser
  gh-pages par publier.py, vérifier version.json en ligne, bumper le CACHE du service
  worker si l'appli coupe a bougé, diffuser le kit aux satellites. À charger dès qu'on
  parle de publier, mettre en ligne, régénérer le site ou toucher l'appli coupe.
---

# Publier le portail

`site/public/` n'est pas versionné : il est reconstruit en entier et poussé de
force sur `gh-pages` en un commit jetable. `main` porte la vraie histoire.

## 1. Avant : les planches

```bash
python3 site/outils/reprendre_plans.py --verifier   # ce que publier.py fera
python3 site/outils/reprendre_plans.py              # si une image est plus vieille que son PDF
```

`publier.py` **refuse** de pousser une image plus vieille que la planche dont
elle sort — c'est arrivé le 03/09/2026 pour cinq planches du dust-shoe,
régénérées le 01/09. Les PNG rafraîchis vont dans `site/contenu/captures/`
et se **commitent** sur `main`.

## 2. Si l'appli coupe a bougé

`site/appli/coupe/index.html` est servie telle quelle sur `/coupe/` et installée
hors-ligne par un service worker. **Incrémenter `const CACHE = "coupe-vNN"`
dans `sw.js`** à chaque retouche, sinon les appareils gardent l'ancienne
version ; `generer.py` lit ce numéro et écrit `version.json`. Le calcul de la
page doit rester **identique à `coupe_noyau.py`** de `~/Projets/logiciels/vitesses-coupe`
(même table `MATS`, mêmes formules ; `tests_jumeau_web.py` là-bas le rejoue
sous node). La marque `<!--CHAPEAU_VERDIER-->` et `{{VERSION}}` doivent
rester : la génération s'arrête sinon.

## 3. Publier

```bash
python3 site/publier.py          # régénère + force-push gh-pages
python3 site/publier.py --sec    # régénère seulement
```

Puis vérifier en ligne, GitHub Pages met une à deux minutes :

```bash
curl -s "https://atelierduverdier.fr/coupe/version.json?$(date +%s)"
```

Pas de préproduction : **relire dans un navigateur** ce qui a changé. Les
défauts les plus coûteux (bandeau invisible en sombre, planche périmée)
n'étaient ni dans le Markdown ni dans la sortie du vérificateur.

## 4. Le kit vers les satellites

```bash
python3 outils/diffuser_kit.py --blanc    # dit ce qu'il ferait
python3 outils/diffuser_kit.py            # pose les verdier-* chez laser, PrintNC, liens
```

Il s'arrête sur une divergence (`.kit-empreintes.json`) au lieu d'écraser, ne
touche **jamais au HTML** des satellites, préfixe tout `verdier-*` (une
première version avait écrasé `assets/logo.svg` du site laser). Une retouche se
fait dans `kit/` puis se rediffuse, jamais chez le satellite. Jetons seuls chez
PrintNC et liens : la charte entière leur faisait grandir la page de 258 px.

## 5. Ne jamais

Recopier une valeur à la main (version LaserAtelier lue dans `laser_core.py`,
matières lues dans l'appli, cotes lues dans le `.FCStd`) ; toucher au `CNAME`
d'un satellite ; éditer `site/public/`. Commits en français sans accents,
poussés sur `main` (skill `commit-atelier`).
