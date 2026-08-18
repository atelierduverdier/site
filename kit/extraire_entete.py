#!/usr/bin/env python3
# =========================================================================
# extraire_entete.py — tire verdier-entete.css de verdier.css
# =========================================================================
# POURQUOI UN TROISIÈME FICHIER. `extraire_jetons.py` donne les couleurs à
# un site qui a déjà sa mise en page — c'est ce qu'il fallait au journal
# PrintNC, dont le kit entier faisait grandir la page de 258 px. Mais les
# jetons seuls ne portent PAS la barre du haut, et c'est elle qui fait le
# chemin du retour vers le portail.
#
# Relevé le 18/08/2026 : le journal citait `atelierduverdier.fr` cinq fois,
# et les CINQ étaient `laser.atelierduverdier.fr`. Zéro lien vers la racine
# du domaine. Un visiteur venu d'un reel Instagram était dans un cul-de-sac.
# Le site laser avait la barre, mais sa marque pointait sur `#top` : elle
# ramenait en haut de la même page, jamais à l'atelier.
#
# Ce fichier extrait la SECTION 3 de verdier.css — l'en-tête, et rien
# d'autre : la barre collante, la marque, les liens, le bouton de thème et
# le menu replié en étroit. Un site qui charge verdier.css en entier n'en a
# pas besoin ; un site à jetons seuls, si.
#
# CE QU'IL SUPPOSE CHEZ L'HÔTE : une classe `.wrap` (conteneur centré). La
# règle posée ici est `.topbar .wrap`, qui ajoute la disposition en ligne
# et la hauteur — elle ne crée pas le conteneur. Le journal a la sienne,
# large de 820 px : la barre s'aligne donc sur sa colonne, ce qui est
# exactement ce qu'on veut.
#
# UTILISATION : python3 kit/extraire_entete.py
# =========================================================================

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
SOURCE = KIT / 'verdier.css'
CIBLE = KIT / 'verdier-entete.css'

# Les bornes de la section, telles qu'elles sont écrites dans verdier.css.
# Si un jour ces bandeaux changent, ce script s'arrête au lieu de produire
# un fichier vide qui laisserait la barre sans style, sans le dire.
# `/*` doit être échappé : en expression régulière, `/*` vaut « zéro ou
# plusieurs `/` », et la borne tombait alors un caractère trop loin — la
# section sortait sans son ouverture de commentaire, et traînait le `/*`
# de la section suivante. Un commentaire jamais fermé, en fin de fichier :
# le navigateur l'avale sans rien dire.
DEBUT = r'/\* ---------- 3\. En-tête'
FIN = r'/\* ---------- 4\. Héros'

# Les sélecteurs qu'on doit retrouver, sinon la section n'est pas celle
# qu'on croit. `.brand` porte le lien vers le portail, `.brand-sub` nomme
# le satellite : sans eux le fichier ne sert à rien.
ATTENDUS = ['header.topbar', '.brand', '.brand-sub', '.navlinks', '.theme-btn']

ENTETE = """/* L'EN-TÊTE de la charte de l'Atelier du Verdier, et rien d'autre.

   Extrait de verdier.css par kit/extraire_entete.py — ne pas éditer, ni
   ici ni dans la copie posée chez un satellite : corriger verdier.css et
   relancer l'extraction.

   Ce fichier va avec verdier-jetons.css, pour les sites qui gardent leur
   mise en page mais veulent la barre du haut commune — celle qui porte le
   chemin du retour vers atelierduverdier.fr. Un site qui charge
   verdier.css en entier l'a déjà : ne pas ajouter les deux.

   Il suppose que le site fournit `.wrap`, son conteneur centré. */

"""


def main() -> None:
    css = SOURCE.read_text(encoding='utf-8')

    d = re.search(DEBUT, css)
    f = re.search(FIN, css)
    if not d or not f:
        sys.exit("extraire_entete : bandeau de section introuvable dans "
                 "verdier.css — la section « 3. En-tête » a-t-elle été "
                 "renommée ?")
    if f.start() < d.start():
        sys.exit("extraire_entete : la section 4 précède la section 3.")

    section = css[d.start():f.start()].rstrip() + '\n'

    # Une règle de héros dort dans cette section : `.hero-art svg.logo`,
    # posée là parce qu'elle parle du même logo. Elle n'a rien à faire
    # dans une barre du haut, et chez un satellite qui a son propre héros
    # elle irait se battre avec lui. On la laisse à la source — c'est le
    # seul retrait, et il est nommé plutôt que deviné.
    section = re.sub(r'^\.hero-art [^\n{]*\{[^}]*\}\n', '', section,
                     flags=re.M)

    manquants = [s for s in ATTENDUS if s not in section]
    if manquants:
        sys.exit(f"extraire_entete : sélecteurs absents de la section — "
                 f"{', '.join(manquants)}")
    if '.hero' in section:
        sys.exit("extraire_entete : il reste une règle de héros dans la "
                 "section 3 — la retirer à la source, ou l'ajouter au "
                 "filtre de ce script.")

    CIBLE.write_text(ENTETE + section, encoding='utf-8')
    n = len(re.findall(r'\{', CIBLE.read_text(encoding='utf-8')))
    print(f"  {CIBLE.name} : {n} règles, "
          f"{CIBLE.stat().st_size // 1024} Ko")


if __name__ == '__main__':
    main()
