#!/usr/bin/env python3
# =========================================================================
# valeurs_atc.py — lit les grandeurs du magasin ATC DEPUIS LE MODÈLE
# =========================================================================
# La page projets/magasin-atc.html ne doit contenir aucun nombre recopié.
# Tout vient de `note_calcul.valeurs()` du projet magasin-atc, qui les
# calcule à partir des paramètres du modèle — la même fonction qui engendre
# la note de calcul en PDF.
#
# POURQUOI DES BOUCHONS. `magasin_er20` importe FreeCAD et Part au
# chargement, et l'interpréteur de l'AppImage n'est disponible que si
# FreeCAD tourne — son point de montage change à chaque lancement. Or
# `valeurs()` ne touche que des constantes et des fonctions pures
# (trigonométrie). Deux modules factices suffisent donc à l'importer avec le
# python du système, et le site se régénère sans dépendre de FreeCAD.
#
# Si un jour `valeurs()` se met à construire de la géométrie, l'import
# échouera bruyamment — c'est voulu : mieux vaut une génération qui
# s'arrête qu'une page aux nombres périmés.
# =========================================================================

import math
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chemins

CODE_ATC = chemins.ATC_CODE

_cache = None


def _bouchonner_freecad() -> None:
    """Rend `import FreeCAD` inoffensif, le temps de lire les paramètres."""
    for nom in ('FreeCAD', 'Part', 'FreeCADGui', 'Draft', 'Sketcher'):
        if nom in sys.modules:
            continue
        module = types.ModuleType(nom)
        module.__getattr__ = lambda _attr, _n=nom: types.SimpleNamespace()
        sys.modules[nom] = module
    sys.modules['FreeCAD'].Vector = lambda *a, **k: None
    sys.modules['FreeCAD'].Console = types.SimpleNamespace(
        PrintMessage=lambda *a: None,
        PrintWarning=lambda *a: None,
        PrintError=lambda *a: None,
    )


def charger() -> dict:
    """Les grandeurs du modèle, plus quelques dérivées utiles à la page."""
    global _cache
    if _cache is not None:
        return _cache

    if not CODE_ATC.is_dir():
        sys.exit(f"valeurs_atc : projet ATC introuvable ({CODE_ATC}).\n"
                 f"La page magasin-atc ne peut pas être engendrée sans lui.")

    _bouchonner_freecad()
    sys.path.insert(0, str(CODE_ATC))
    try:
        import note_calcul
    except Exception as erreur:                       # pragma: no cover
        sys.exit(f"valeurs_atc : impossible de lire le modèle ATC — "
                 f"{type(erreur).__name__} : {erreur}")

    v = dict(note_calcul.valeurs())

    # Dérivées : la page raisonne en RAYONS là où le modèle donne des
    # diamètres. Calculées ici, jamais écrites dans la page.
    v['r_angles'] = v['sur_angles'] / 2.0
    v['r_chambre'] = v['chambre'] / 2.0
    v['r_bille_seule'] = v['bille'] / 2.0
    v['loge_d'] = v['bille'] + v['poche_jeu']
    v['postes'] = int(round(v['l6'] / v['pas']))
    v['billes_total'] = v['postes'] * 3

    _cache = v
    return v


def nombre(valeur: float, decimales: int = 2) -> str:
    """Format français : virgule décimale, pas de séparateur de milliers."""
    return f"{valeur:.{decimales}f}".replace('.', ',')


def table_saillie() -> str:
    """Le tableau des saillies possibles, ENGENDRÉ depuis le modèle.

    Les bornes, le partage exact et la valeur retenue viennent tous des
    paramètres : changer BILLE_SAILLIE dans le modèle déplace la ligne en
    gras, sans toucher à cette page.
    """
    v = charger()
    s_min, s_max = v['s_min'], v['s_max']
    retenu, equilibre = v['saillie'], v['s_equilibre']

    essais = sorted({s_min, 0.50, retenu, equilibre, 1.50, 2.00, s_max})
    lignes = []
    for s in essais:
        mordant, jeu = s - s_min, s_max - s
        if abs(s - retenu) < 1e-9:
            note, gras = 'retenu', True
        elif abs(s - equilibre) < 1e-9:
            note, gras = 'partage exact', False
        elif abs(s - s_min) < 1e-9:
            note, gras = 'les angles passent : rien ne bloque', False
        elif abs(s - s_max) < 1e-9:
            note, gras = 'les plats ne passent plus', False
        else:
            note, gras = '', False

        cells = [nombre(s), nombre(mordant), nombre(jeu)]
        if gras:
            cells = [f'<b>{c}</b>' for c in cells]
            note = f'<b>{note}</b>'
        lignes.append(
            '<tr>'
            + ''.join(f'<td class="num">{c}</td>' for c in cells)
            + f'<td>{note}</td></tr>'
        )
    return '\n          '.join(lignes)


if __name__ == '__main__':
    v = charger()
    print(f"{len(v)} grandeurs lues depuis {CODE_ATC}")
    for cle in ('saillie', 'mordant', 'jeu_plats', 's_min', 's_max', 's_fenetre',
                's_equilibre', 'passage', 'sur_angles', 'angle_centre', 'porte',
                'marge_bas', 'marge_haut', 'h_arete'):
        print(f"  {cle:<14} {nombre(v[cle])}")
