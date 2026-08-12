#!/usr/bin/env python3
# =========================================================================
# faire_logo.py — compose le logo « chapeau + Atelier du Verdier »
# =========================================================================
# Le logo est ENGENDRÉ, pas dessiné à la main : le chapeau est repris
# verbatim de kit/chapeau.svg, et le mot-symbole est vectorisé depuis une
# police. Deux fichiers en sortent, forcément cohérents entre eux :
#
#   kit/logo.svg          autonome — couleurs figées, avec un @media pour
#                         le thème sombre. Pour l'extérieur : dépôt GitHub,
#                         Ko-fi, carte de visite, avatar.
#   kit/logo-inline.svg   mot-symbole en `currentColor`, sans style interne.
#                         C'est celui que le générateur du site colle DANS
#                         les pages, pour qu'il suive le bouton de thème et
#                         pas seulement le réglage du système.
#
# LE TEXTE EST CONVERTI EN COURBES. Un logo qui dépend d'une police
# installée change d'aspect d'une machine à l'autre, et disparaît sur un
# poste qui ne l'a pas. Inkscape fait la conversion une fois, ici.
#
# LA POLICE. Fira Sans, sous licence SIL Open Font License — libre d'emploi,
# y compris commercial. Les polices de ~/Projets/archives/Fonts sont écartées
# volontairement : plusieurs sont marquées PERSONAL USE ONLY, ce qui exclut
# un logo d'atelier.
#
# UTILISATION :
#   python3 kit/faire_logo.py            les deux variantes
#   python3 kit/faire_logo.py --apercu   + un PNG de contrôle
# =========================================================================

import re
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent
CHAPEAU = KIT / 'chapeau.svg'

TEXTE = 'Atelier du Verdier'
POLICE = 'Fira Sans SemiBold'
POLICE_REPLI = 'Fira Sans'

# --- Géométrie du montage -------------------------------------------------
# Le chapeau occupe HAUTEUR_CHAPEAU unités de haut ; le mot-symbole est
# dimensionné pour que ses capitales fassent à peu près la moitié — au-delà,
# le texte écrase le chapeau ; en deçà, il devient une légende.
HAUTEUR_CHAPEAU = 46.0
CORPS = 30.0            # taille de police, unités du dessin
INTERLETTRE = 0.2       # respiration : un mot-symbole se lit de loin
ECART = 13.0            # entre le bord droit du chapeau et la première lettre
MARGE = 4.0

ENCRE_CLAIRE = '#2f3540'   # ardoise, la couleur de texte de la charte
ENCRE_SOMBRE = '#e6e9ee'


def chapeau() -> tuple:
    """Rend (contenu, x, y, largeur, hauteur) du chapeau.

    Les identifiants Inkscape (`id="g7"`, `id="path3"`…) sont RETIRÉS. Le
    logo est collé plusieurs fois dans une même page — barre du haut et pied
    — et des identifiants dupliqués rendent le document invalide. Vérifié
    avant de les enlever : rien ne les référence, ni `url(#…)` ni
    `href="#…"`. La géométrie et les couleurs, elles, ne bougent pas.
    """
    s = CHAPEAU.read_text(encoding='utf-8')
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    x, y, w, h = (float(t) for t in vb.split())
    corps = s[s.index('<g'):s.rindex('</svg>')].strip()

    if re.search(r'url\(#|href="#', corps):
        sys.exit("faire_logo : le chapeau référence désormais ses propres "
                 "identifiants — ne plus les retirer sans revoir ce code.")
    corps = re.sub(r'\s+id="[^"]*"', '', corps)
    return corps, x, y, w, h


def vectoriser(texte: str) -> tuple:
    """Convertit le texte en courbes via Inkscape. Rend (paths, largeur)."""
    brut = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="200">
  <text x="0" y="150" font-family="{POLICE}, {POLICE_REPLI}, sans-serif"
        font-size="{CORPS}" letter-spacing="{INTERLETTRE}"
        style="font-variant-ligatures:none">{texte}</text>
</svg>'''

    with tempfile.TemporaryDirectory() as tmp:
        entree, sortie = Path(tmp) / 'in.svg', Path(tmp) / 'out.svg'
        entree.write_text(brut, encoding='utf-8')
        r = subprocess.run(
            ['inkscape', '--export-type=svg', '--export-plain-svg',
             '--export-text-to-path', f'--export-filename={sortie}', str(entree)],
            capture_output=True, text=True)
        if not sortie.exists():
            sys.exit(f"faire_logo : Inkscape n'a rien produit.\n{r.stderr[:400]}")
        produit = sortie.read_text(encoding='utf-8')

    chemins = re.findall(r'<path[^>]*\sd="([^"]+)"', produit)
    if not chemins:
        sys.exit("faire_logo : aucune courbe en sortie — le texte n'a pas été "
                 f"vectorisé. La police « {POLICE} » est-elle installée ?")

    # Inkscape peut envelopper les lettres dans un <g transform="...">.
    trans = re.search(r'<g[^>]*transform="(translate\([^)]*\))"', produit)
    enveloppe = trans.group(1) if trans else None

    boite = mesurer(chemins, enveloppe)
    return chemins, enveloppe, boite


def mesurer(chemins, enveloppe) -> tuple:
    """Boîte englobante réelle des courbes, mesurée par Inkscape.

    Calculée sur le dessin, jamais estimée depuis la chaîne : les jambages
    et les accents ne se devinent pas.
    """
    corps = ''.join(f'<path d="{d}"/>' for d in chemins)
    if enveloppe:
        corps = f'<g transform="{enveloppe}">{corps}</g>'
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="200">'
           f'{corps}</svg>')
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / 'm.svg'
        f.write_text(doc, encoding='utf-8')
        r = subprocess.run(['inkscape', '--query-all', str(f)],
                           capture_output=True, text=True)
    xs, ys, x2s, y2s = [], [], [], []
    for ligne in r.stdout.splitlines():
        p = ligne.split(',')
        if len(p) == 5:
            try:
                x, y, w, h = (float(v) for v in p[1:])
            except ValueError:
                continue
            xs.append(x); ys.append(y); x2s.append(x + w); y2s.append(y + h)
    if not xs:
        sys.exit("faire_logo : impossible de mesurer le mot-symbole.")
    return min(xs), min(ys), max(x2s) - min(xs), max(y2s) - min(ys)


def composer(inline: bool) -> str:
    ch, cx, cy, cw, chh = chapeau()
    chemins, enveloppe, (tx, ty, tw, th) = vectoriser(TEXTE)

    k = HAUTEUR_CHAPEAU / chh                      # chapeau à sa taille voulue
    ch_w, ch_h = cw * k, HAUTEUR_CHAPEAU

    x_texte = MARGE + ch_w + ECART
    y_texte = MARGE + ch_h / 2.0 + th / 2.0        # centré sur le chapeau

    largeur = x_texte + tw + MARGE
    hauteur = MARGE * 2 + ch_h

    corps_texte = ''.join(f'<path d="{d}"/>' for d in chemins)
    if enveloppe:
        corps_texte = f'<g transform="{enveloppe}">{corps_texte}</g>'

    if inline:
        style = ''
        remplissage = 'currentColor'
    else:
        style = (f'\n  <style>\n'
                 f'    .mot{{fill:{ENCRE_CLAIRE}}}\n'
                 f'    @media (prefers-color-scheme: dark){{ .mot{{fill:{ENCRE_SOMBRE}}} }}\n'
                 f'  </style>')
        remplissage = None

    attr = (f'class="mot"' if remplissage is None else f'fill="{remplissage}"')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- Logo de l'Atelier du Verdier — ENGENDRÉ par kit/faire_logo.py.
     Ne pas retoucher à la main : relancer le script.
     Chapeau repris verbatim de kit/chapeau.svg (noir, liseré blanc, bande
     orange) — il ne se repeint pas. Mot-symbole : {POLICE}, converti en
     courbes, donc indépendant des polices du poste.
     {'Variante EN LIGNE : le mot suit currentColor.' if inline
       else 'Variante AUTONOME : couleurs figées + @media pour le thème sombre.'} -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largeur:.1f} {hauteur:.1f}"
     width="{largeur:.0f}" height="{hauteur:.0f}"{' class="logo"' if inline else ''}
     role="img" aria-label="Atelier du Verdier">
  <title>Atelier du Verdier</title>{style}
  <g transform="translate({MARGE:.1f} {MARGE:.1f}) scale({k:.5f}) translate({-cx:.3f} {-cy:.3f})">
    {ch}
  </g>
  <g {attr} transform="translate({x_texte - tx:.2f} {y_texte - ty - th:.2f})">
    {corps_texte}
  </g>
</svg>
'''


def main() -> None:
    for inline, nom in ((False, 'logo.svg'), (True, 'logo-inline.svg')):
        chemin = KIT / nom
        chemin.write_text(composer(inline), encoding='utf-8')
        print(f"  {nom:<18} {chemin.stat().st_size:>6} o")
        subprocess.run(['xmllint', '--noout', str(chemin)], check=True)

    if '--apercu' in sys.argv:
        # La variante EN LIGNE tire sa couleur de la page (currentColor). Hors
        # page elle retomberait sur du noir — invisible sur fond sombre, ce qui
        # ferait un aperçu mensonger. On la rend donc dans une enveloppe qui
        # pose la couleur, exactement comme le fera le site.
        inline = (KIT / 'logo-inline.svg').read_text(encoding='utf-8')
        inline = inline[inline.index('<svg'):]
        for fond, encre, nom in (('#ffffff', ENCRE_CLAIRE, 'apercu-clair.png'),
                                 ('#14171b', ENCRE_SOMBRE, 'apercu-sombre.png')):
            with tempfile.TemporaryDirectory() as tmp:
                f = Path(tmp) / 'a.svg'
                f.write_text(inline.replace('<svg ', f'<svg color="{encre}" ', 1),
                             encoding='utf-8')
                subprocess.run(['rsvg-convert', '-w', '760', '-b', fond,
                                '-o', str(KIT / nom), str(f)], check=True)
            print(f"  {nom:<18} fond {fond}, encre {encre}")


if __name__ == '__main__':
    main()
