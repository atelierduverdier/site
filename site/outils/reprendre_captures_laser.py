#!/usr/bin/env python3
# =========================================================================
# reprendre_captures_laser.py — reprend les captures de LaserAtelier
# =========================================================================
# Contrairement aux deux autres logiciels, LaserAtelier a DÉJÀ ses captures :
# elles vivent dans son dépôt et servent son propre site. On ne les
# régénère donc pas ici — on les reprend.
#
# LA SOURCE EST `docs/manuel_img/`, PAS `docs/screenshots/`.
#
#   docs/manuel_img/       les 22 panneaux, recadrés pour tenir dans un
#                          document (430 × 240 à 760). Régénérés par
#                          `python3 tests/lancer.py --captures`, qui passe
#                          par le harnais des tests : config redirigée vers
#                          une copie jetable, donc capturer ne peut pas
#                          écrire dans les mesures au pied à coulisse.
#
#   docs/screenshots/*.png quatre captures plein écran de FreeCAD. Écartées :
#                          elles dataient du 16 juillet 2026 et le script ne
#                          les régénère pas. Entre-temps le panneau des
#                          préférences est passé de 519 à 1 978 px et la
#                          grille de test de 760 à 2 526 — les montrer
#                          reviendrait à illustrer un atelier qui n'existe
#                          plus.
#
# Aucun redimensionnement : 430 px est déjà la largeur juste, et le passage
# en WebP est fait par generer.py au moment de publier.
#
# UTILISATION :
#   python3 site/outils/reprendre_captures_laser.py
# =========================================================================

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chemins

SOURCE = chemins.LASER_IMG
SORTIE = Path(__file__).resolve().parent.parent / 'contenu' / 'captures'

# Les panneaux repris, et pourquoi chacun. Six sur vingt-deux : de quoi
# montrer l'étendue sans transformer la page en galerie.
REPRISES = [
    ('testgrid.png',     'laser-p-grille-test.png'),    # mesurer avant de calculer
    ('curved.png',       'laser-p-marquage.png'),       # la raison d'être : surfaces courbes
    ('halftone.png',     'laser-p-photo.png'),          # les huit tramages
    ('defocus.png',      'laser-p-defocus.png'),        # la calibration du défocus
    ('nuancier.png',     'laser-p-nuancier.png'),       # la planche de tons
    ('calligraphie.png', 'laser-p-calligraphie.png'),   # le plus récent
]

# Les anciennes reprises, à effacer si elles traînent encore.
PERIMEES = ['laser-grille-test.png', 'laser-job-combine.png',
            'laser-panneau-photo.png', 'laser-resultat.png']


def main() -> None:
    if not SOURCE.is_dir():
        sys.exit(f"reprendre_captures_laser : {SOURCE} introuvable.\n"
                 f"Lancer d'abord, depuis le dépôt LaserAtelier :\n"
                 f"    python3 tests/lancer.py --captures")

    SORTIE.mkdir(parents=True, exist_ok=True)

    for nom in PERIMEES:
        vieille = SORTIE / nom
        if vieille.exists():
            vieille.unlink()
            print(f"  retirée : {nom}")

    total = 0
    for nom_source, nom_cible in REPRISES:
        src = SOURCE / nom_source
        if not src.exists():
            print(f"  ! absente : {nom_source}")
            continue
        shutil.copy2(src, SORTIE / nom_cible)
        taille = src.stat().st_size
        total += taille
        print(f"  {nom_cible:<30} {taille // 1024:>4} Ko")

    print(f"\n{len(REPRISES)} panneau(x) repris — {total // 1024} Ko "
          f"(avant conversion WebP)")


if __name__ == '__main__':
    main()
