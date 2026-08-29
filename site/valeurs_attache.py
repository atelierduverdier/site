#!/usr/bin/env python3
# =========================================================================
# valeurs_attache.py — les cotes de l'attache de descente, LUES à la source
# =========================================================================
# CE MODÈLE N'A PAS DE TABLEUR, et c'est pour ça que ce fichier existe à côté
# de valeurs_fcstd.py au lieu d'en être un cas de plus. Le meuble et la
# tonnelle sont pilotés par une feuille « Cotes » dans le document : lire
# leur .py donnerait un chiffre de départ, périmé. L'attache, elle, est
# engendrée de bout en bout par `construire_attache.py` — la vérité est dans
# son bloc PARAMÈTRES, et nulle part ailleurs.
#
# On ne lit pourtant PAS le .py : deux des chiffres qui comptent — la masse
# de chaque pièce — ne se déduisent que des solides, une fois FreeCAD passé.
# Le script écrit donc `valeurs.json` à chaque construction, et c'est ce
# fichier qu'on lit ici. Aucun chiffre n'est recopié, et le site n'a besoin
# ni de FreeCAD ni de Blender pour se construire.
#
# UNE CLÉ INCONNUE ARRÊTE LA GÉNÉRATION. Mieux vaut pas de page qu'une page
# où il manque un nombre — ou pire, où il en traîne un d'avant.
# =========================================================================

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chemins

_cache = {}


def _charger() -> dict:
    if _cache:
        return _cache
    source = chemins.ATTACHE_VALEURS
    if not source.is_file():
        sys.exit(f"valeurs_attache : {source} introuvable — le produire avec "
                 f"`python3 construire_attache.py` dans le dépôt de l'attache.")
    _cache.update(json.loads(source.read_text(encoding='utf-8')))
    _cache.update(_variantes())
    return _cache


def _variantes() -> dict:
    """Les autres tailles engendrées à côté de la principale.

    Le dépôt écrit un `valeurs-<diamètre>-<fixation>.json` par variante
    construite. ON LES COMPTE PLUTÔT QUE DE LES ÉCRIRE : « Ø 63, Ø 80 et
    Ø 100 » tapé dans la page serait faux le jour où une taille s'ajoute, et
    personne ne rouvrirait la phrase pour vérifier. C'est la règle de la
    maison appliquée à une liste au lieu d'un nombre.

    Rend `diametres` (« Ø 63, Ø 80 et Ø 100 ») et `vis_ordinaire` (« 6 × 70 »,
    lu dans le nom de fixation de la variante à vis).
    """
    fichiers = sorted(chemins.ATTACHE.glob('valeurs-*.json'))
    if not fichiers:
        return {}
    diams, vis = {_cache.get('d_tube')}, set()
    for f in fichiers:
        d = json.loads(f.read_text(encoding='utf-8'))
        diams.add(d.get('d_tube'))
        m = re.match(r'vis (\d+)x(\d+)$', str(d.get('fixation', '')))
        if m:
            vis.add('%s × %s' % m.groups())
    diams = [int(x) for x in sorted(d for d in diams if d)]
    if len(diams) > 1:
        liste = ('Ø ' + ', Ø '.join(str(x) for x in diams[:-1])
                 + ' et Ø ' + str(diams[-1]))
    else:
        liste = 'Ø ' + str(diams[0])
    dehors = {'diametres': liste, 'nb_diametres': len(diams)}
    if len(vis) == 1:
        dehors['vis_ordinaire'] = vis.pop()
    return dehors


def valeur(cle: str, decimales: int = 1) -> str:
    """`{{attache.alesage}}` -> « 81 », `{{attache.prise_filet}}` -> « 4,7 »."""
    v = _charger()
    if cle not in v:
        sys.exit(f"valeurs_attache : clé « {cle} » inconnue. Disponibles : "
                 + ', '.join(sorted(v)))
    x = v[cle]
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return ' × '.join(_fr(c, decimales) for c in x)
    return _fr(x, decimales)


def _fr(x, decimales: int) -> str:
    if isinstance(x, int) or float(x).is_integer():
        return str(int(x))
    return ('%.*f' % (decimales, x)).replace('.', ',')


def toutes() -> dict:
    return dict(_charger())


if __name__ == '__main__':
    for c, v in sorted(toutes().items()):
        print(f"  {c:<16} {v}")
