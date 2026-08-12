#!/usr/bin/env python3
# =========================================================================
# valeurs_fcstd.py — lit les cotes DANS le tableur d'un document FreeCAD
# =========================================================================
# Le meuble à balais et la tonnelle sont pilotés par un tableur « Cotes » :
# on change une valeur, on recalcule, la pièce suit. Leur `construire_*.py`
# porte bien des constantes, mais ce ne sont que des valeurs de DÉPART —
# le fichier le dit lui-même : « une fois le document construit, la vérité
# est dans le tableur ». Lire le .py donnerait donc un chiffre périmé, ce
# qui est exactement le piège qu'on passe son temps à éviter ici.
#
# COMMENT, SANS FREECAD. Un .FCStd est une archive zip, et son Document.xml
# porte les cellules du tableur en clair. On les lit donc directement, sans
# l'AppImage et sans que FreeCAD ait besoin de tourner.
#
# CE QU'ON N'A PAS. Les cellules contiennent la FORMULE (« =2000 mm »), pas
# le résultat calculé. Une valeur littérale se lit très bien ; une formule
# qui référence d'autres cellules, non — et dans ce cas on refuse plutôt
# que de deviner. Voir `nombre()`.
# =========================================================================

import html
import re
import sys
import zipfile
from pathlib import Path

_cache = {}


def _feuilles(fcstd: Path) -> dict:
    """{ nom de feuille -> { 'B4': 'contenu' } }.

    CLOISONNÉ PAR FEUILLE, et ce n'est pas un détail : le meuble à balais
    porte DEUX tableurs dans le même document, `Parametres` (les entrées,
    littérales) et `Cotes` (du calculé). Leurs cellules ont les mêmes
    adresses. Une première version mettait tout dans un seul dictionnaire
    et la seconde feuille écrasait la première — l'alias `Hauteur` se
    retrouvait en face du libellé « Largeur du toit ». Rien n'a été publié
    ainsi : l'incohérence s'est vue au contrôle.
    """
    if fcstd in _cache:
        return _cache[fcstd]
    if not fcstd.exists():
        sys.exit(f"valeurs_fcstd : {fcstd} introuvable.")
    with zipfile.ZipFile(fcstd) as z:
        xml = z.read('Document.xml').decode('utf-8', 'replace')

    # Chaque <Object name="X"> ouvre un objet ; ses cellules sont celles
    # qui suivent, jusqu'à l'objet nommé suivant.
    bornes = [(m.group(1), m.start())
              for m in re.finditer(r'<Object name="([^"]+)"', xml)]
    feuilles = {}
    for k, (nom, debut) in enumerate(bornes):
        fin = bornes[k + 1][1] if k + 1 < len(bornes) else len(xml)
        bloc = xml[debut:fin]
        cellules = {a: html.unescape(c) for a, c in
                    re.findall(r'<Cell address="([A-Z]+\d+)"[^>]*?content="([^"]*)"', bloc)}
        if cellules:
            feuilles[nom] = cellules
    if not feuilles:
        sys.exit(f"valeurs_fcstd : aucun tableur dans {fcstd.name}.")
    _cache[fcstd] = feuilles
    return feuilles


def _cellules(fcstd: Path, feuille: str = None) -> dict:
    """Les cellules d'UNE feuille. Sans nom : la première qui en a."""
    f = _feuilles(fcstd)
    if feuille:
        if feuille not in f:
            sys.exit(f"valeurs_fcstd : feuille « {feuille} » absente de "
                     f"{fcstd.name}. Présentes : {', '.join(f)}")
        return f[feuille]
    return next(iter(f.values()))


def table(fcstd: Path, feuille: str = None, col_libelle='A',
          col_valeur='B') -> dict:
    """{ libellé -> contenu de la cellule voisine }, lignes vides ignorées.

    Les libellés sont normalisés — minuscules, accents et ponctuation
    retirés — pour qu'une recherche n'échoue pas sur une majuscule ou un
    tiret. Le libellé d'origine est conservé en valeur.
    """
    cellules = _cellules(fcstd, feuille)
    out = {}
    for adresse, contenu in cellules.items():
        m = re.match(rf'^{col_libelle}(\d+)$', adresse)
        if not m:
            continue
        valeur = cellules.get(f'{col_valeur}{m.group(1)}')
        if valeur is None:
            continue
        libelle = contenu.lstrip("'").strip()
        if not libelle:
            continue
        out[_cle(libelle)] = (libelle, valeur.lstrip("'").strip())
    return out


def alias(fcstd: Path) -> dict:
    """{ alias -> contenu }, pour les cellules qui en portent un.

    C'EST LA BONNE ENTRÉE quand le document en a. Un alias est le nom que
    le modèle lui-même utilise dans ses formules : il ne bouge pas quand
    on reformule un libellé, et une cellule qui en porte un est une
    ENTRÉE du modèle, donc une valeur littérale — pas une formule dérivée.

    Le meuble à balais en a 120 ; sa feuille « Cotes » n'est que du
    calculé (`=round(Parametres.Hauteur…)`), inexploitable ici.
    """
    if not fcstd.exists():
        sys.exit(f"valeurs_fcstd : {fcstd} introuvable.")
    with zipfile.ZipFile(fcstd) as z:
        xml = z.read('Document.xml').decode('utf-8', 'replace')
    # L'ordre des attributs n'est pas garanti : on prend la cellule
    # ENTIÈRE, puis on y cherche content et alias séparément.
    out = {}
    for cell in re.findall(r'<Cell\b[^>]*/>', xml):
        al = re.search(r'\balias="([^"]*)"', cell)
        co = re.search(r'\bcontent="([^"]*)"', cell)
        if al and co:
            out[al.group(1)] = html.unescape(co.group(1)).lstrip("'").strip()
    return out


def par_alias(fcstd: Path, nom: str, decimales: int = 0) -> str:
    """La valeur d'un alias, en français. S'arrête si absent ou non numérique."""
    t = alias(fcstd)
    if nom not in t:
        proches = [k for k in t if nom.lower()[:5] in k.lower()][:5]
        sys.exit(f"valeurs_fcstd : alias « {nom} » absent de {fcstd.name}."
                 + (f" Proches : {', '.join(proches)}" if proches else ""))
    m = re.fullmatch(r'=?\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:mm|cm|m)?', t[nom])
    if not m:
        sys.exit(f"valeurs_fcstd : alias « {nom} » vaut « {t[nom]} » — "
                 f"pas un nombre littéral.")
    v = float(m.group(1).replace(',', '.'))
    return f"{v:.{decimales}f}".replace('.', ',')


def _cle(s: str) -> str:
    s = s.lower()
    for a, b in (('à', 'a'), ('â', 'a'), ('é', 'e'), ('è', 'e'), ('ê', 'e'),
                 ('î', 'i'), ('ï', 'i'), ('ô', 'o'), ('û', 'u'), ('ù', 'u'),
                 ('ç', 'c')):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def nombre(fcstd: Path, libelle: str, decimales: int = 0) -> str:
    """La valeur numérique en face d'un libellé, en français.

    S'ARRÊTE plutôt que de deviner : libellé absent, ou cellule contenant
    une formule qui référence d'autres cellules. Un chiffre faux sur une
    page vaut moins que pas de page du tout.
    """
    t = table(fcstd)
    cle = _cle(libelle)
    if cle not in t:
        proches = [v[0] for k, v in t.items() if cle.split()[0] in k][:4]
        sys.exit(f"valeurs_fcstd : « {libelle} » absent de {fcstd.name}."
                 + (f" Voulais-tu : {', '.join(proches)} ?" if proches else ""))

    brut = t[cle][1]
    # « =2000 mm », « 2000 », « =2000mm » — mais pas « =B4-2*C7 ».
    m = re.fullmatch(r'=?\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:mm|cm|m)?', brut)
    if not m:
        sys.exit(f"valeurs_fcstd : « {libelle} » vaut « {brut} » dans "
                 f"{fcstd.name} — une formule, pas un nombre. Ce lecteur ne "
                 f"calcule pas : citer une autre cote, ou publier ce libellé "
                 f"sans son chiffre.")
    v = float(m.group(1).replace(',', '.'))
    return f"{v:.{decimales}f}".replace('.', ',')


if __name__ == '__main__':
    for f in sys.argv[1:]:
        p = Path(f)
        print(f"\n{p.name}")
        for nom, cellules in _feuilles(p).items():
            print(f"  feuille « {nom} » — {len(cellules)} cellules")
        for nom_al, val in list(alias(p).items())[:10]:
            print(f"    alias {nom_al:<18} {val[:34]}")
