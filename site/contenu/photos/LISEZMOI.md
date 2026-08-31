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
   `page de sortie -> (nom du fichier, texte alternatif)`.
3. Régénérer. La ligne `photo … → photos/…` du journal de génération dit
   ce qui a été publié, et à quel poids.

Tant que le fichier n'est pas là, la case du héros reste un **aplat neutre**
au bon format, et la génération le rappelle à chaque passage :

```
! photo du héros absente : …/photos/fraiseuse-en-usinage.jpg
```

Le format d'affichage est un **3/2** recadré en `cover` : la photo n'est
jamais déformée, elle est rognée. Une prise large (paysage) s'y met mieux
qu'un portrait. Pour un autre rapport sur une page donnée, poser
`style="--photo-ratio:16/9"` sur la `<div class="hero-photo">`.

## Attendu aujourd'hui

| fichier | page | ce qu'on veut voir |
|---|---|---|
| `fraiseuse-en-usinage.jpg` | accueil | la PrintNC en train d'usiner, ou la tête laser au travail |
