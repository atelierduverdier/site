#!/usr/bin/env python3
# =========================================================================
# extraire_jetons.py — tire verdier-jetons.css de verdier.css
# =========================================================================
# POURQUOI UN SECOND FICHIER. Le kit est un système de design complet :
# jetons, typographie, boutons, encarts, mise en page. C'est ce qu'il faut
# à un site qui n'a rien, comme le portail. C'est trop pour un site qui a
# déjà le sien, comme le journal PrintNC.
#
# Mesuré le 12/08/2026 en essayant : le kit entier posé sous le journal
# lui ajoutait 258 px, parce que `.hero h1{font-size:2.7rem}` du kit est
# PLUS SPÉCIFIQUE que le `.hero-titre` du journal, qui perdait. Chercher
# ces collisions une par une n'a pas de fin — 17 sélecteurs se croisent,
# et la spécificité en crée d'autres qui ne se voient pas au nom.
#
# Le journal n'a donc besoin que des JETONS : les couleurs de la charte,
# sans sa mise en page. Ce fichier les extrait — il n'est jamais écrit à
# la main, pour que les deux ne puissent pas diverger.
#
# UTILISATION : python3 kit/extraire_jetons.py
# =========================================================================

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
SOURCE = KIT / 'verdier.css'
CIBLE = KIT / 'verdier-jetons.css'

ENTETE = """/* Les JETONS de la charte de l'Atelier du Verdier, et rien d'autre.

   Extrait de verdier.css par kit/extraire_jetons.py — ne pas éditer, ni
   ici ni dans la copie posée chez un satellite : corriger verdier.css et
   relancer l'extraction.

   Ce fichier est fait pour les sites qui ont DÉJÀ leur mise en page et ne
   veulent que les couleurs. Un site qui part de rien charge verdier.css
   en entier. */

"""


def main() -> None:
    css = SOURCE.read_text(encoding='utf-8')

    # Les blocs de jetons : :root, le @media du thème système, et les deux
    # :root[data-theme]. On les prend entiers, accolades comprises.
    blocs = []
    for m in re.finditer(r'(@media \(prefers-color-scheme: dark\)\s*\{.*?\n\}'
                         r'|:root(?:\[data-theme="\w+"\])?\s*\{[^}]*\})',
                         css, re.S):
        bloc = m.group(0)
        if '--' not in bloc:
            continue
        blocs.append(bloc.strip())

    if len(blocs) < 3:
        sys.exit(f"extraire_jetons : {len(blocs)} bloc(s) trouvé(s), au moins 3 "
                 f"attendus (:root, @media sombre, les deux data-theme).")

    CIBLE.write_text(ENTETE + '\n\n'.join(blocs) + '\n', encoding='utf-8')
    n = len(re.findall(r'--[\w-]+\s*:', CIBLE.read_text(encoding='utf-8')))
    print(f"  {CIBLE.name} : {len(blocs)} blocs, {n} jetons, "
          f"{CIBLE.stat().st_size // 1024} Ko")


if __name__ == '__main__':
    main()
