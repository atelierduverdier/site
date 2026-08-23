#!/usr/bin/env python3
# =========================================================================
# rendre_3d.py — une vue 3D de chaque projet, pour le site
# =========================================================================
# Les pages projets ne montraient que des PLANCHES : des dessins au trait,
# justes et illisibles pour qui n'en lit pas. Relevé du 12/08/2026 sur le
# site engendré — meuble : 1 image, une planche ; tonnelle : 1 image, une
# planche ; magasin ATC : 3 planches TechDraw. **Aucune page ne montrait
# l'objet en tant qu'objet.** Les pages logiciels, elles, ont 3 à 6 vraies
# captures chacune : le déséquilibre était là, pas dans le compte.
#
# Ce script prend la vue 3D du modèle FreeCAD lui-même. Rien n'est modelé
# ici et rien n'est enregistré : le modèle reste la seule source.
#
# TROIS PIÈGES PAYÉS EN L'ÉCRIVANT :
#
#  1. `ActiveView` n'est PAS la vue 3D. Un document dont la dernière vue
#     ouverte était une planche rend un `MDIViewPagePy`, qui n'a ni
#     `viewIsometric` ni `saveImage`. Il faut demander explicitement
#     `mdiViewsOfType('Gui::View3DInventor')`.
#  2. Il faut `FreeCADGui.showMainWindow()` : sans elle, pas de vue du tout.
#     Le rendu marche en `QT_QPA_PLATFORM=offscreen`, donc sans écran.
#  3. On travaille sur une COPIE. Ouvrir ne modifie rien, mais un plantage
#     d'OCC pendant le rendu ne doit pas pouvoir toucher un modèle qui porte
#     des heures d'établi.
#
# UTILISATION (le python de l'AppImage, pas celui du système) :
#   QT_QPA_PLATFORM=offscreen \
#     ~/Applications/FreeCAD_*.appimage --console site/outils/rendre_3d.py
#
# Le verdict se lit dans /tmp/rendre_3d.txt : la console de FreeCAD avale la
# sortie et ne remonte pas le code.
# =========================================================================

import os
import shutil
import tempfile
import traceback
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
SORTIE = RACINE / 'site' / 'contenu' / 'captures'
JOURNAL = Path(tempfile.gettempdir()) / 'rendre_3d.txt'

LARGEUR, HAUTEUR = 1600, 1200

# (nom sur le site, modèle FreeCAD, ce que la vue montre)
#
# DEUX MODÈLES, PAS TROIS. Le magasin ATC a été essayé et ÉCARTÉ : son
# document s'ouvre avec 216 objets visibles sur 516, et ce qui reste allumé
# ne compose rien — le rendu sortait quasiment blanc, avec une plaque et une
# pièce isolée. C'est le piège déjà noté dans son propre CLAUDE.md : masquer
# un corps PartDesign ne suffit pas, il faut aussi sa `Tip`, et l'assemblage
# vit dans un groupe « Assemblage monte » qu'il faudrait rallumer pièce par
# pièce. Sa page porte déjà trois planches TechDraw — c'est la mieux
# illustrée des trois. Mieux vaut deux images justes qu'une troisième vide.
MODELES = [
    ('vue3d-tonnelle',
     Path.home() / 'Projets/realisations/tonnelle-jasmin/Tonnelle.FCStd',
     "la tonnelle montée, poteaux, sablières, chevrons et plots"),
    ('vue3d-meuble',
     Path.home() / 'Projets/realisations/meuble-balais/MeubleABalais.FCStd',
     "l'armoire de jardin, bardage et toit"),
]

# L'ANGLE EST CELUI DE `viewIsometric()`, ET C'EST UNE LIMITE ASSUMÉE.
# `setViewDirection` permettrait de choisir le coin, mais il ne préserve pas
# la verticale : essayé sur quatre directions le 12/08/2026, le vecteur
# « haut » sort quelconque et le meuble se couche. Composer une rotation
# autour de Z avec `setCameraOrientation` donne, elle, une vue de dessus.
# Conséquence à connaître : sur le meuble, l'isométrique par défaut montre
# deux faces bardées et PAS la porte, qui est sur la face latérale gauche.
# La planche d'ensemble de sa page, elle, la montre. À reprendre le jour où
# quelqu'un saura poser proprement direction ET verticale.

_lignes = []


def dire(texte):
    _lignes.append(texte)
    print(texte, flush=True)
    JOURNAL.write_text("\n".join(_lignes) + "\n", encoding='utf-8')


def rendre(nom, modele, quoi, bac):
    import FreeCAD
    import FreeCADGui

    if not modele.is_file():
        return f"{nom} : modèle introuvable — {modele}"

    copie = bac / modele.name
    shutil.copy2(modele, copie)

    doc = FreeCAD.openDocument(str(copie))
    vues = FreeCADGui.ActiveDocument.mdiViewsOfType('Gui::View3DInventor')
    if not vues:
        FreeCAD.closeDocument(doc.Name)
        return f"{nom} : ce document n'a aucune vue 3D"

    v = vues[0]
    v.viewIsometric()
    v.fitAll()
    cible = SORTIE / f'{nom}.png'
    v.saveImage(str(cible), LARGEUR, HAUTEUR, 'White')
    FreeCAD.closeDocument(doc.Name)

    if not cible.exists() or cible.stat().st_size < 5000:
        return f"{nom} : image absente ou vide"
    dire(f"  {cible.name:<24} {cible.stat().st_size // 1024:>5} Ko   {quoi}")
    return None


def main():
    import FreeCADGui
    # AVANT tout : sans elle, FreeCADGui n'a même pas d'`ActiveDocument`, et
    # aucun document ne reçoit de vue. Une fois pour toutes les vues.
    FreeCADGui.showMainWindow()

    SORTIE.mkdir(parents=True, exist_ok=True)
    bac = Path(tempfile.mkdtemp(prefix='rendre_3d_'))
    soucis = []
    try:
        for nom, modele, quoi in MODELES:
            try:
                s = rendre(nom, modele, quoi, bac)
            except Exception:
                s = f"{nom} : {traceback.format_exc().strip().splitlines()[-1]}"
            if s:
                soucis.append(s)
                dire(f"  ÉCHEC  {s}")
    finally:
        shutil.rmtree(bac, ignore_errors=True)

    dire("")
    if soucis:
        dire(f"ÉCHEC — {len(soucis)} modèle(s) sur {len(MODELES)}")
        return 1
    dire(f"{len(MODELES)} vue(s) 3D rendues dans contenu/captures/.")
    return 0


# PAS de garde `if __name__ == "__main__":`. La console de FreeCAD exécute
# avec un autre `__name__` : le garde ne se déclenche pas, le script ne fait
# RIEN, et le processus sort avec 0. Piège déjà payé deux fois aujourd'hui.
_code = 1
try:
    _code = main()
except Exception:
    dire("ÉCHEC — exception :\n" + traceback.format_exc())
dire(f"(code {_code})")
raise SystemExit(_code)
