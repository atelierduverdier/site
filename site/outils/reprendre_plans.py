#!/usr/bin/env python3
# =========================================================================
# reprendre_plans.py — reprend les planches d'ensemble des projets
# =========================================================================
# RIEN N'EST RENDU ICI. Les projets engendrent déjà leurs planches depuis
# leur modèle FreeCAD, et ces planches portent déjà ce qu'il faut : les
# élévations cotées, la vue de dessus, ET une perspective. Refaire un rendu
# 3D à côté serait une seconde vérité à tenir à jour.
#
# On reprend donc la page d'ensemble de chaque PDF, en image.
#
# POURQUOI PNG ET PAS SVG. `pdftocairo -svg` rend un fichier de 2,2 Mo pour
# la planche du meuble — chaque hachure y devient un chemin. La même page
# en PNG 150 dpi puis WebP sans perte fait 65 Ko, et le trait reste net.
# Mesuré, pas supposé. Le PNG est déposé dans contenu/captures/ ; c'est
# generer.py qui le passe en WebP au moment de publier, comme les autres.
#
# UTILISATION :
#   python3 site/outils/reprendre_plans.py
# =========================================================================

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
SORTIE = RACINE / 'site' / 'contenu' / 'captures'
RESOLUTION = 150          # dpi ; au-delà le WebP grossit sans gagner en lisibilité

# (nom sur le site, PDF source, page, ce que la planche montre)
PLANCHES = [
    ('plan-meuble-ensemble',
     Path.home() / 'Projets' / 'realisations' / 'meuble-balais' / 'Plan_Ensemble.pdf',
     1, "élévations, dessus, perspective et tableau des cotes"),
    ('plan-tonnelle-ensemble',
     Path.home() / 'Projets' / 'realisations' / 'tonnelle-glycine' / 'docs' / 'plans.pdf',
     1, "élévation de face, vue de dessus, côté et perspective"),
]


def main() -> None:
    if not subprocess.run(['which', 'pdftoppm'], capture_output=True).returncode == 0:
        sys.exit("reprendre_plans : il faut pdftoppm (paquet poppler).")

    SORTIE.mkdir(parents=True, exist_ok=True)
    total = 0
    for nom, pdf, page, quoi in PLANCHES:
        if not pdf.exists():
            print(f"  ! absent : {pdf}")
            continue

        # pdftoppm ajoute son propre suffixe de page : on l'enlève ensuite.
        prefixe = SORTIE / nom
        r = subprocess.run(['pdftoppm', '-r', str(RESOLUTION), '-png',
                            '-f', str(page), '-l', str(page),
                            str(pdf), str(prefixe)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"reprendre_plans : pdftoppm a échoué sur {pdf.name}\n{r.stderr}")

        produits = sorted(SORTIE.glob(f'{nom}-*.png'))
        if not produits:
            sys.exit(f"reprendre_plans : aucune image produite pour {pdf.name}.")
        cible = SORTIE / f'{nom}.png'
        produits[0].replace(cible)
        for reste in produits[1:]:
            reste.unlink()

        total += cible.stat().st_size
        print(f"  {cible.name:<30} {cible.stat().st_size // 1024:>5} Ko   {quoi}")

    print(f"\n{len(PLANCHES)} planche(s), {total // 1024} Ko en PNG "
          f"(generer.py les passera en WebP)")


if __name__ == '__main__':
    main()
