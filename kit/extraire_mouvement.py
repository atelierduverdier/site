#!/usr/bin/env python3
# =========================================================================
# extraire_mouvement.py — tire verdier-mouvement.css de verdier.css
# =========================================================================
# POURQUOI UN TROISIÈME EXTRAIT. Le mouvement ajouté à la charte le
# 27/08/2026 est ce qui se voit le plus : les blocs montent doucement en
# entrant dans le champ. Un satellite qui ne prend que les JETONS reçoit
# pourtant `verdier.js`, donc la classe `.js-reveal` lui est bien posée sur
# les éléments — mais sans règle en face, elle ne fait RIEN. Le site
# recevait la mécanique sans l'effet.
#
# Lui donner `verdier.css` en entier n'est pas la réponse : c'est
# exactement la leçon des 258 px du 12/08/2026 (voir extraire_jetons.py).
#
# La section 13bis est donc coupée en deux dans la source. `13bis-a` ne
# nomme QUE des choses que le kit écrit lui-même — `.js-reveal` par
# verdier.js, `data-agrandir` par la visionneuse — plus deux règles sur des
# éléments bruts. Aucune collision possible avec la feuille d'un hôte.
# `13bis-b` s'appuie sur `.carte`, `.hero`, `.btn` : elle reste à la maison.
#
# CE QUI SE PASSE SI QUELQU'UN AJOUTE UNE RÈGLE DANS 13bis-a. Elle part sur
# quatre sites au prochain `diffuser_kit.py`. Le garde-fou ci-dessous ne
# vérifie que la PRÉSENCE des règles attendues : il ne peut pas juger
# qu'une règle nouvelle est portable. C'est écrit en toutes lettres dans le
# bandeau de 13bis-a, côté verdier.css — l'endroit où on l'aurait sous les
# yeux au moment d'écrire.
#
# UTILISATION : python3 kit/extraire_mouvement.py
# =========================================================================

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
SOURCE = KIT / 'verdier.css'
CIBLE = KIT / 'verdier-mouvement.css'

# Les bornes de la part portable, telles qu'elles sont écrites dans
# verdier.css. Si ces bandeaux changent, ce script s'ARRÊTE au lieu de
# produire un fichier vide qui laisserait les blocs invisibles chez les
# satellites — la panne la plus vicieuse que ce kit puisse causer, parce
# qu'elle ne se voit que chez quelqu'un d'autre.
#
# `/*` est échappé : en expression régulière `/*` vaut « zéro ou plusieurs
# `/` », et la borne tombe alors un caractère trop loin (voir
# extraire_entete.py, qui a payé ce piège).
DEBUT = r'/\* ---------- 13bis-a\. Portable'
FIN = r'/\* ---------- 13bis-b\. Maison'

# Sans ces trois-là, le fichier ne sert à rien : la classe qui cache, celle
# qui montre, et la coupure pour qui ne supporte pas le mouvement.
#
# LES DEUX PREMIÈRES SONT ANCRÉES EN DÉBUT DE LIGNE, et ce n'est pas du
# zèle. Écrites en simple sous-chaîne, elles se validaient toutes seules :
# `.js-reveal.vu{` se retrouve tel quel DANS la ligne
# `.js-reveal,.js-reveal.vu{` du bloc `prefers-reduced-motion`. En
# renommant la vraie règle, le garde-fou restait vert — il ne contrôlait
# rien. Vu au sabotage le 27/08/2026, pas à la relecture.
ATTENDUS = [r'^\.js-reveal\{', r'^\.js-reveal\.vu\{',
            r'prefers-reduced-motion']

# CE QUI NE DOIT JAMAIS S'Y TROUVER : les classes de mise en page du kit.
# Ce garde-fou-là attrape la vraie faute — quelqu'un qui range une règle
# dans la mauvaise moitié — alors que ATTENDUS n'attrape qu'une section
# vidée par erreur.
INTERDITS = ['.carte', '.panel', '.hero', '.btn', '.wrap', '.navlinks',
             '.figure', '.plan', '.capture', '.liens']

ENTETE = """/* Le MOUVEMENT de la charte de l'Atelier du Verdier, la part portable.

   Extrait de verdier.css (section 13bis-a) par kit/extraire_mouvement.py —
   ne pas éditer, ni ici ni dans la copie posée chez un satellite :
   corriger verdier.css et relancer l'extraction.

   Ce fichier va avec verdier-jetons.css et verdier.js, pour les sites qui
   gardent leur mise en page. Il ne nomme que ce que le kit écrit lui-même :
   rien ici ne peut entrer en collision avec la feuille de l'hôte. Un site
   qui charge verdier.css en entier l'a déjà : ne pas ajouter les deux.

   Il a BESOIN de verdier.js : c'est le script qui pose `.js-reveal`, et
   seulement s'il sait l'animer. Poser ce fichier SANS le script ne cache
   rien (aucun élément ne porte la classe) ; poser la classe à la main dans
   le HTML rendrait le contenu invisible chez qui n'exécute pas le script.

   Les jetons `--sortie` et `--leve` viennent de verdier-jetons.css. */

"""


def main() -> None:
    css = SOURCE.read_text(encoding='utf-8')

    d = re.search(DEBUT, css)
    f = re.search(FIN, css)
    if not d or not f:
        sys.exit("extraire_mouvement : bornes introuvables dans verdier.css "
                 f"(début {'vu' if d else 'ABSENT'}, fin {'vue' if f else 'ABSENTE'}). "
                 "Les bandeaux 13bis-a / 13bis-b ont-ils été renommés ?")
    if f.start() <= d.start():
        sys.exit("extraire_mouvement : la fin précède le début.")

    part = css[d.start():f.start()].rstrip() + '\n'

    manquants = [a for a in ATTENDUS
                 if not re.search(a, part, re.M)]
    if manquants:
        sys.exit(f"extraire_mouvement : {manquants} absent(s) de 13bis-a — "
                 "la section n'est pas celle qu'on croit.")

    # On cherche les interdits dans le CODE seul : le bandeau de 13bis-a
    # les cite justement pour dire de ne pas les mettre là.
    code = re.sub(r'/\*.*?\*/', '', part, flags=re.S)
    fautifs = [i for i in INTERDITS if i in code]
    if fautifs:
        sys.exit(f"extraire_mouvement : {fautifs} trouvé(s) dans 13bis-a. "
                 "Ces classes supposent la mise en page du kit et casseraient "
                 "un satellite : les déplacer dans 13bis-b.")

    CIBLE.write_text(ENTETE + part, encoding='utf-8')
    n = len(re.findall(r'\{', code))
    print(f"  {CIBLE.name} : {n} règles, {CIBLE.stat().st_size} octets")


if __name__ == '__main__':
    main()
