# atelierduverdier.fr — le portail et la charte commune

Site statique engendré par un script Python maison, servi par GitHub Pages sur
**<https://atelierduverdier.fr>**. Il porte l'accueil, les fiches des quatre
logiciels de l'atelier, la rubrique projets — et **la charte que les autres
sites recopient**.

L'atelier a quatre sites. Celui-ci est la racine ; les autres gardent leur doc
chez eux, sur leur sous-domaine :

| domaine | dépôt |
|---|---|
| `atelierduverdier.fr` | **ici** |
| `printnc.atelierduverdier.fr` | [`printnc-build`](https://github.com/atelierduverdier/printnc-build) — journal de construction |
| `laser.atelierduverdier.fr` | [`LaserAtelier`](https://github.com/atelierduverdier/LaserAtelier)`/docs` |
| `liens.atelierduverdier.fr` | [`liens`](https://github.com/atelierduverdier/liens) |

Fédérer plutôt que fusionner : la doc de LaserAtelier vit dans le dépôt du
greffon, ce qui garantit qu'elle suive sa `VERSION`. On ne casse pas ça pour
une question de mise en page.

## Publier

```bash
python3 site/publier.py        # régénère, puis force-push sur gh-pages
python3 site/generer.py        # régénère seulement, dans site/public/
```

`site/public/` est **entièrement reconstruit** à chaque passage et n'est pas
versionné. La source est `site/contenu/` et `kit/` ; rien ne s'y édite à la
main.

## Ce qui n'est jamais recopié à la main

C'est la règle de la maison, et elle vient d'une ligne `VERSION` restée
44 versions en retard dans un fichier qui la recopiait. Une valeur écrite deux
fois finit toujours par diverger.

| ce qui est affiché | lu à la génération dans |
|---|---|
| la version de LaserAtelier | `laser_core.py` du greffon |
| les cotes des projets FreeCAD | le **tableur** du `.FCStd`, pas le script |
| les chiffres du magasin ATC | `note_calcul.valeurs()` du projet |
| les planches et vues 3D | les modèles FreeCAD eux-mêmes |

Une clé absente **arrête** la génération. Rien d'à moitié engendré ne part en
ligne.

Trois garde-fous du même esprit :

* `reprendre_plans.py --verifier` refuse de publier si l'image d'une planche
  est plus vieille que le PDF dont elle sort. Une planche corrigée s'est
  affichée des heures durant dans sa version d'avant : l'image existait, elle
  était simplement périmée.
* les captures portent l'**empreinte de leur contenu** dans leur nom
  (`plan-tonnelle-ensemble.1d3add22.webp`). Un nom qui ne change pas est un
  mensonge que le cache répète.
* le kit se **diffuse par script**, jamais à la main — voir plus bas.

## La charte

`kit/` porte `verdier.css`, ses jetons, `verdier.js`, le chapeau et le logo.
`outils/diffuser_kit.py` les recopie chez les satellites avec un bandeau
« engendré, ne pas éditer ici » :

* **site laser** — la charte entière ;
* **journal PrintNC** — les **jetons** + `verdier-entete.css`. La charte
  complète lui faisait grandir la page de 258 px : dix-sept sélecteurs du kit
  gagnaient sur les siens. Il garde sa mise en page et ses quatre couleurs de
  phase, qui sont des accents de contenu ;
* **page de liens** — les **jetons** + `verdier-entete.css` aussi, depuis le
  18/08/2026. Elle n'était pas un cul-de-sac : sa première carte mène à
  l'atelier. Ce qui a tranché n'est pas le chemin du retour mais que les
  **quatre adresses se ressemblent** — même marque, même sous-titre qui dit
  où l'on est. Sa carte reste sa carte.

**Les quatre sous-titres :** rien (le portail) · Journal PrintNC · Atelier
Laser · Mes liens.

`verdier-entete.css` est tiré de `verdier.css` par `kit/extraire_entete.py`,
comme les jetons le sont par `kit/extraire_jetons.py` — la section « en-tête »
et rien d'autre, pour les sites à jetons seuls. Il existe parce que les jetons
ne portent pas la barre du haut, **et que c'est elle qui fait le chemin du
retour**. Relevé le 18/08/2026 : le journal citait `atelierduverdier.fr` cinq
fois, et les cinq étaient `laser.atelierduverdier.fr` ; la marque du site laser
pointait sur `#top`. Depuis la bascule du 12/08 la racine sert le portail —
personne arrivé d'un reel Instagram n'avait de porte de sortie vers l'atelier.

Le HTML, lui, se branche **à la main, une fois, avec les yeux dessus** :
`diffuser_kit.py` ne touche jamais aux pages. Trois choses mesurées au
navigateur en le faisant, qu'aucune relecture n'aurait données :

* le journal avait une règle `header{padding:70px 0 44px}` qui réclamait
  **tous** les `<header>` — la barre en héritait et faisait 175 px au lieu
  de 60, recouvrant les onglets. Portée à `header:not(.topbar)` ;
* `.topbar .wrap` avait une hauteur **fixe** : les neuf liens du site laser
  passaient à deux lignes sous 1052 px de fenêtre et débordaient par-dessous.
  Passée en `min-height` — le portail, quatre liens sur une ligne, n'en voit
  rien ;
* les ancres `#doc-…` du journal atterrissaient sous les barres collantes.
  La marge de défilement est désormais **mesurée** par son JS, parce qu'elle
  change avec l'onglet (128 px sur Documentation, 265 px sur Timeline).

## Outils

| | |
|---|---|
| `site/generer.py` | assemble les pages, convertit les captures en WebP |
| `site/publier.py` | régénère et pousse sur `gh-pages` |
| `site/outils/rendre_3d.py` | vues 3D des projets, prises dans FreeCAD sans écran |
| `site/outils/reprendre_plans.py` | planches TechDraw des projets, en image |
| `site/outils/capturer_*.py` | captures des logiciels, application lancée hors écran |
| `outils/diffuser_kit.py` | recopie la charte chez les satellites |
| `kit/faire_logo.py` | compose le logo, texte converti en courbes |

Ceux qui touchent à FreeCAD se lancent avec le python de l'AppImage :

```bash
QT_QPA_PLATFORM=offscreen ~/Applications/FreeCAD_*.appimage --console site/outils/rendre_3d.py
```

Ces fichiers-là n'ont **pas** de garde `if __name__ == "__main__":` : la console
de FreeCAD exécute avec un autre `__name__`, le garde ne se déclencherait pas,
le script ne ferait rien et sortirait avec 0 — un silence qui ressemble à un
succès.

## Le plan

[`PLAN.md`](PLAN.md) porte le cadrage, les six décisions structurantes et
l'état des chantiers. Il fait foi sur ce qui reste à faire.
