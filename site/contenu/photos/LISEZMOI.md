# Les photos de l'atelier

Ici vivent les **photos** que le site sert — pas les captures d'écran, qui
sont dans `../captures/`, ni les rendus de modèles, qui sortent de FreeCAD.

`generer.py` les publie dans `public/photos/` : converties en WebP, bornées
à 1400 px de large, et **nommées par l'empreinte de leur contenu** — la même
règle que partout ailleurs ici. Une photo remplacée sous le même nom
continuerait sinon de s'afficher dans sa version d'avant.

## En déposer une

1. Copier le fichier ici (`.jpg` ou `.png`, le plus grand qu'on ait :
   la réduction se fait à la génération, jamais l'inverse).
2. Nommer la photo dans `PHOTOS_HEROS`, en tête de `site/generer.py` —
   `page de sortie -> {fichier, alt, ratio}`. **Le nom doit correspondre au
   fichier déposé** : une photo qui s'appelle autrement n'est pas trouvée, et
   la génération le dit sans s'arrêter (c'est arrivé au premier essai, le
   31/08/2026 — `printnc.jpg` déposé, `fraiseuse-en-usinage.jpg` attendu,
   et le site est parti en ligne avec son aplat).
3. Régénérer. La ligne `photo … → photos/…` du journal de génération dit
   ce qui a été publié, et à quel poids.

Tant que le fichier n'est pas là, la case du héros reste un **aplat neutre**
au bon format, et la génération le rappelle à chaque passage :

```
! photo du héros absente : …/photos/fraiseuse-en-usinage.jpg
```

Le format d'affichage est recadré en `cover` : la photo n'est jamais
déformée, elle est **rognée**. Le rapport par défaut est un **3/2** ; la clé
`ratio` de `PHOTOS_HEROS` en impose un autre, et c'est là qu'il faut regarder
la photo avant de choisir. Un panorama dans une case 3/2 perd ses bords —
`printnc.jpg` fait 2,22 et y aurait laissé 227 px de chaque côté, c'est-à-dire
le chariot de l'axe Y et le bout du portique. Il est servi en `2/1`.

| rapport | hauteur dans le héros (466 px de large) | rogné sur une photo 2,22 |
|---|---|---|
| `3/2` | 311 px | 227 px par bord |
| `16/9` | 262 px | 139 px par bord |
| `2/1` | 233 px | 69 px par bord |

## Attendu aujourd'hui

| fichier | page | rapport | ce qu'on voit |
|---|---|---|---|
| `printnc.jpg` | accueil | `2/1` | la PrintNC entière sur son établi, lit martyr et portique |
