# Faire un rendu, de FreeCAD à Blender

Trois chaînes existent dans ce dépôt et elles ne font pas la même chose. La
première question est de savoir laquelle tu veux.

| ce que tu veux | l'outil | le temps |
|---|---|---|
| une vignette pour une page projet | `rendre_3d.py` | instantané |
| un objet à faire tourner dans le navigateur | `exporter_glb.py` | ~1 min |
| **une belle image, ombres et matières** | `exporter_glb.py` **puis** `rendre_blender.py` | ~5 s de rendu |

`rendre_3d.py` prend la vue 3D de FreeCAD telle quelle : plat, gratuit, sans
ombre. `rendre_blender.py` est ce qui suit — il ne le remplace pas.

---

## La procédure, en deux commandes

### 1. FreeCAD → un GLB coloré

```bash
cd ~/Projets/site/Site_AtelierDuVerdier
xvfb-run -a freecad --console site/outils/exporter_glb.py
```

Le verdict est dans `/tmp/exporter_glb.txt` — la console de FreeCAD avale la
sortie et ne remonte pas le code. Les GLB atterrissent dans
`site/contenu/modeles/`.

**Pourquoi passer par le GLB plutôt que d'exporter des STL à la main :** il
porte les COULEURS. Un STL n'en a pas, et tu les reposerais une à une dans
Blender à chaque fois.

### 2. GLB → une image

```bash
blender --background --factory-startup \
  --python site/outils/rendre_blender.py -- \
  site/contenu/modeles/dust-shoe.glb ~/Images/sabot.png
```

Options, après les deux tirets :

| option | défaut | ce que ça fait |
|---|---|---|
| `--taille` | `1600x1200` | pixels |
| `--azimut` | `35` | degrés autour de l'objet |
| `--hauteur` | `25` | degrés au-dessus de l'horizon |
| `--echantillons` | `128` | qualité ; 32 suffit pour cadrer, 256 pour livrer |
| `--fond` | `blanc` | `transparent`, ou une couleur `#e8e8e8` |
| `--sol` | `oui` | `non` pour un objet qui flotte |
| `--film` | `standard` | `agx` pour une image d'ambiance |

Mesuré sur la RX 7600M XT : **5 secondes** pour 900 × 700 à 96 échantillons,
sur le GPU en HIP. Le script le détecte seul et retombe sur le processeur en
le disant.

---

## Si tu veux le faire à la main, dans Blender

Pour art-diriger — changer une matière, poser une vraie table, essayer un
HDRI. Le script fait exactement ces étapes ; les refaire à la main ne demande
que de ne pas oublier la troisième.

1. **Importer** : `Fichier ▸ Importer ▸ glTF 2.0`, prendre le `.glb`. Les
   pièces arrivent avec leurs couleurs, chacune sa matière.
2. **Cadrer** : sélectionner tout (`A`), puis `Vue ▸ Cadrer les éléments
   sélectionnés`, et `Ctrl+Alt+0` pour poser la caméra sur la vue courante.
3. **LA TRANSFORMATION DE VUE** — `Propriétés de rendu ▸ Gestion des
   couleurs ▸ Transformation de vue : Standard`. Sans ça, voir plus bas.
4. **Moteur** : Cycles, périphérique GPU. `Préférences ▸ Système ▸ Cycles ▸
   HIP` doit lister la Radeon.
5. **Le sol** : un plan sous l'objet, coché **Receveur d'ombre** dans
   `Propriétés d'objet ▸ Visibilité`, et **sans matière**.
6. **Lumière** : trois surfaces (clé, débouchage, contre-jour) plutôt qu'une
   seule. Le script les place à 1,4 / 2,0 / 0,6 rayon.

---

## Les six pièges, tous payés

**1. La transformation de vue AgX.** Blender l'applique par défaut : c'est un
film qui compresse les hautes lumières. Un fond **blanc pur en ressort à
196,196,196** — mesuré au pixel. J'ai d'abord accusé le plan d'ombre, puis le
monde ; c'était le tone mapping. `Standard` rend ce qu'on demande.

**2. Les couleurs viennent du DOCUMENT, pas du script.** Un `.FCStd` écrit
sans interface n'embarque pas de `GuiDocument.xml` : ses pièces naissent
invisibles ET grises. Le modèle sort alors au gris d'usine `(0,447 0,475
0,502)` sans qu'aucune erreur ne le dise. **Régénère toujours avec
`xvfb-run`**, jamais en `QT_QPA_PLATFORM=offscreen python3`.

**3. Un receveur d'ombre ne doit pas porter de matière.** Sinon elle est
éclairée, et c'est elle qu'on voit : le fond blanc ressortait gris dégradé.
Sans matière, il ne montre que l'ombre.

**4. `camera_to_view_selected` n'existe pas en arrière-plan.** Il exige une
vue 3D, absente avec `--background` — d'où le cadrage calculé : rayon de la
sphère englobante, puis distance pour qu'elle tienne dans le champ.

**5. L'énergie des lampes va comme le CARRÉ de la taille.** Le même réglage
brûle un collier de 8 cm et laisse un cabanon de 2 m dans le noir. Le script
la met à l'échelle ; à la main, souviens-t'en.

**6. L'export glTF de FreeCAD marche — mais pas depuis un script.** Ce
fichier a d'abord affirmé le contraire, et Christophe l'a démenti le
29/08/2026 en exportant son porte-manteau : un `.gltf` de 15 Ko avec son
`.bin` de 46 Ko, engendré par OCCT 7.9, **et sa vraie couleur bois**
(0,571 0,342 0,133 — pas un gris d'usine).

Remesuré aussitôt : `Import.export` sort bien 1,1 Mo pour l'assemblage du
sabot, six maillages. La phrase « 320 octets, buffer à zéro » était fausse.

**Ce qui reste vrai, et qui est la raison de l'étape Blender :** appelé
DEPUIS UN SCRIPT, cet export ne pose **aucun matériau**. Mesuré sur quatre
documents — l'assemblage du sabot, l'attache et ses quatre pièces, un corps
PartDesign seul, trois corps du cabanon — tous avec des `ShapeColor` bien
posées : `materiaux = 0` à chaque fois. L'export de Christophe, lui, est
passé par le MENU de l'interface.

La différence entre les deux chemins n'est pas encore expliquée. Tant qu'elle
ne l'est pas, la chaîne garde Blender, qui reçoit les couleurs par un
manifeste et ne dépend d'aucun de ces deux comportements.

---

## Ce que ça donne

Le sabot d'aspiration parqué, 900 × 700, 96 échantillons, 5 s :
fond blanc pur, ombre portée douce, et les six pièces à leurs vraies
couleurs — adaptateur `#ff8a00`, semelle bleue, quai vert.
