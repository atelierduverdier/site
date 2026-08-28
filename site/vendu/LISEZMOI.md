# vendu/ — les bibliothèques tierces, servies depuis le site

## model-viewer.min.js

`<model-viewer>` de Google, **version 4.0.0**, LICENCE BSD-3-Clause.
955 Ko bruts, **250 Ko servis en gzip** (mesuré).

Il est **vendu avec le site plutôt que tiré d'un CDN**, pour la même raison
que l'appli « vitesses de coupe » : le site doit rester entier sans dépendre
d'un tiers, et une page qui charge un script d'ailleurs raconte à ce tiers
qui la visite.

Il n'est chargé que par la page des modèles 3D — c'est tout l'intérêt de les
avoir rassemblés sur une seule page plutôt que dispersés : le visiteur qui ne
veut pas de 3D ne paie rien.

Pour le mettre à jour :

    curl -sL -o model-viewer.min.js \
      https://unpkg.com/@google/model-viewer@<version>/dist/model-viewer.min.js

et vérifier ensuite dans le navigateur que les modèles chargent encore et que
les couleurs n'ont pas bougé — c'est ce contrôle-là qui a révélé, la première
fois, que les couleurs sortaient en linéaire.
