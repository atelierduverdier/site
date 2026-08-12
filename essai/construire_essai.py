#!/usr/bin/env python3
# =========================================================================
# construire_essai.py — assemble la page d'essai de la charte
# =========================================================================
# Colle kit/entete.html + corps.html + kit/pied.html en remplaçant les
# marques {{...}}. Volontairement minuscule : le but est de VÉRIFIER que
# les gabarits du kit s'assemblent, pas de préfigurer le générateur du
# site — celui-là viendra au chantier 1 et lira de vraies données.
#
# UTILISATION :
#   python3 essai/construire_essai.py
# Produit : essai/index.html, à ouvrir dans un navigateur.
# =========================================================================

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
KIT = RACINE / 'kit'
ESSAI = RACINE / 'essai'
SORTIE = ESSAI / 'index.html'

# Depuis essai/index.html, le kit est un cran au-dessus.
VERS_KIT = '../kit/'

NAV = '\n      '.join(
    f'<a href="#{ancre}">{libelle}</a>'
    for ancre, libelle in [
        ('logiciels', 'Logiciels'),
        ('composants', 'Composants'),
        ('top', 'Haut'),
    ]
)

LIENS_PIED = '\n      '.join([
    '<a href="https://github.com/atelierduverdier">GitHub</a>',
    '<a href="https://laser.atelierduverdier.fr">Site laser</a>',
    '<a href="https://atelierduverdier.fr">Journal PrintNC</a>',
])

VALEURS_ENTETE = {
    'TITRE': "Banc d'essai — charte Atelier du Verdier",
    'DESCRIPTION': "Page d'essai de la charte commune : tous les composants du kit "
                   "sur une seule page, pour être jugés à l'écran.",
    'RACINE': VERS_KIT,
    'SOUS_TITRE': "banc d'essai",
    'NAV': NAV,
    'LOCAL_CSS': '',
}

VALEURS_PIED = {
    'RACINE': VERS_KIT,
    'SOUS_TITRE': "banc d'essai",
    'RESUME': "Page d'essai de la charte commune. Rien ici n'est en ligne.",
    'LIENS': LIENS_PIED,
    'ANNEE': '2026',
    'LOCAL_JS': '',
}


def remplir(gabarit: str, valeurs: dict, nom: str) -> str:
    """Remplace les {{MARQUES}} et refuse de laisser passer un trou.

    Une marque oubliée s'afficherait telle quelle sur la page — visible,
    mais seulement si on relit. Autant s'arrêter tout de suite.
    """
    for cle, valeur in valeurs.items():
        gabarit = gabarit.replace('{{' + cle + '}}', valeur)

    restantes = set(re.findall(r'\{\{(\w+)\}\}', gabarit))
    if restantes:
        sys.exit(f"{nom} : marque(s) non remplacée(s) : {', '.join(sorted(restantes))}")
    return gabarit


def main() -> None:
    entete = remplir((KIT / 'entete.html').read_text(encoding='utf-8'),
                     VALEURS_ENTETE, 'entete.html')
    corps = (ESSAI / 'corps.html').read_text(encoding='utf-8')
    pied = remplir((KIT / 'pied.html').read_text(encoding='utf-8'),
                   VALEURS_PIED, 'pied.html')

    SORTIE.write_text(entete + '\n' + corps + '\n' + pied, encoding='utf-8')
    print(f"écrit : {SORTIE.relative_to(RACINE)}  ({SORTIE.stat().st_size} octets)")
    print(f"à ouvrir : file://{SORTIE}")


if __name__ == '__main__':
    main()
