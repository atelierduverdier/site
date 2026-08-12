#!/usr/bin/env python3
# =========================================================================
# chemins.py — où vivent les projets dont le site tire sa matière
# =========================================================================
# UN SEUL ENDROIT, et c'est tout l'intérêt. Le 12/08/2026, ~/Projets a été
# rangé en logiciels/ machine/ realisations/ site/ archives/, et six chemins
# absolus se sont retrouvés périmés dans TROIS fichiers différents :
# generer.py, valeurs_atc.py, outils/capturer_*.py. L'outil de réécriture
# avait bien corrigé les commentaires et le JSON, mais pas les
# constructions `Path.home() / 'Projets' / 'x'` — découpées en fragments
# entre guillemets, elles lui étaient invisibles.
#
# La génération, elle, l'a dit tout de suite : `valeurs_atc` a REFUSÉ de
# produire la page ATC plutôt que de la publier sans ses nombres. C'est le
# garde-fou qui a fait son travail.
#
# Au prochain rangement : ce fichier, et lui seul.
#
# `verifier()` liste tout ce qui manque d'un coup, au lieu de le découvrir
# une erreur à la fois.
# =========================================================================

from pathlib import Path

PROJETS = Path.home() / 'Projets'

# --- Les dépôts ----------------------------------------------------------
MAGASIN_ATC = PROJETS / 'machine' / 'magasin-atc'
GRAPHTEC = PROJETS / 'logiciels' / 'graphtec-ce6000'
VISUALISEUR = PROJETS / 'logiciels' / 'visualiseur-gcode'
LASER_ATELIER = (Path.home() / '.local' / 'share' / 'FreeCAD' / 'v1-1'
                 / 'Mod' / 'LaserAtelier')

# --- Ce qu'on y lit ------------------------------------------------------
ATC_CODE = MAGASIN_ATC / 'code'                    # note_calcul.valeurs()
ATC_PLANS = MAGASIN_ATC / 'plans' / 'er20'         # planches TechDraw
ATC_PERCAGE = MAGASIN_ATC / 'gcode' / 'percage_lit_atc.ngc'
LASER_CORE = LASER_ATELIER / 'laser_core.py'       # la VERSION
LASER_IMG = LASER_ATELIER / 'docs' / 'manuel_img'  # les 22 panneaux

# Les projets d'atelier dont les cotes vivent dans le tableur de leur
# document FreeCAD — lues par valeurs_fcstd, sans que FreeCAD tourne.
TONNELLE_FCSTD = (PROJETS / 'realisations' / 'tonnelle-glycine' / 'Tonnelle.FCStd')
MEUBLE_FCSTD = (PROJETS / 'realisations' / 'meuble-balais' / 'MeubleABalais.FCStd')
DUST_SHOE = PROJETS / 'machine' / 'dust-shoe'

# Un gros fichier d'atelier, pour montrer le visualiseur en charge.
PAQUERETTE = (PROJETS / 'archives' / 'Conception' / 'FreeCAD' / 'Penderie'
              / 'paquerette2.ngc')

# nom lisible -> chemin, pour le contrôle groupé
TOUT = {
    'dépôt magasin ATC': MAGASIN_ATC,
    'code ATC (note de calcul)': ATC_CODE,
    'planches ATC': ATC_PLANS,
    'G-code perçage du lit': ATC_PERCAGE,
    'dépôt Graphtec': GRAPHTEC,
    'dépôt visualiseur': VISUALISEUR,
    'dépôt LaserAtelier': LASER_ATELIER,
    'laser_core.py (VERSION)': LASER_CORE,
    'panneaux LaserAtelier': LASER_IMG,
    'paquerette2.ngc': PAQUERETTE,
    'modèle tonnelle': TONNELLE_FCSTD,
    'modèle meuble à balais': MEUBLE_FCSTD,
    'dossier dust shoe': DUST_SHOE,
}


def verifier() -> list:
    """Rend la liste des (nom, chemin) qui n'existent pas."""
    return [(nom, c) for nom, c in TOUT.items() if not c.exists()]


if __name__ == '__main__':
    manquants = verifier()
    for nom, chemin in TOUT.items():
        etat = 'OK    ' if chemin.exists() else 'ABSENT'
        print(f"  {etat}  {nom:<28} {chemin}")
    print(f"\n{len(TOUT) - len(manquants)}/{len(TOUT)} présents")
    if manquants:
        raise SystemExit(f"{len(manquants)} chemin(s) à corriger dans ce fichier.")
