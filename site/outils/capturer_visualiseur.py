#!/usr/bin/env python3
# =========================================================================
# capturer_visualiseur.py — copies d'écran du visualiseur G-code
# =========================================================================
# S'appuie sur l'outil du projet lui-même, `outils/capturer.py`, qui sait
# composer l'habillage Qt et le tampon OpenGL — un `grab()` ordinaire ne
# traverse pas la vue 3D. Ce script ne fait que l'appeler quatre fois, avec
# les fichiers et les réglages qui racontent le mieux le programme.
#
# IL FAUT `rs274`. Le visualiseur n'interprète pas le G-code : il délègue à
# l'interpréteur de LinuxCNC. Depuis le 12/08/2026 c'est le paquet AUR
# `linuxcnc`, natif dans /usr/bin — le conteneur distrobox a été supprimé.
# Sans rs274 dans le PATH, aucune capture.
#
# HORS ÉCRAN via QT_QPA_PLATFORM=offscreen. Rien n'apparaît sur le bureau.
#
# UN MOT SUR LE CODE DE SORTIE : capturer.py écrit son PNG puis meurt en
# core dump à la fermeture — un défaut de démontage OpenGL hors écran, sans
# effet sur l'image. On juge donc sur l'EXISTENCE du fichier et sa
# fraîcheur, pas sur le code de retour.
#
# UTILISATION :
#   python3 site/outils/capturer_visualiseur.py
# =========================================================================

import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chemins

PROJET = chemins.VISUALISEUR
SORTIE = Path(__file__).resolve().parent.parent / 'contenu' / 'captures'

PERCAGE = chemins.ATC_PERCAGE
PAQUERETTE = chemins.PAQUERETTE

# Un fichier volontairement fautif : `K` dans un arc du plan XY. C'est
# l'exemple même que cite le projet pour expliquer pourquoi il AJOUTE une
# raison au message de rs274 — « K word given for arc in xy plane » est
# exact, mais n'apprend rien à qui veut juste tailler une pièce.
#
# Fichier RÉEL et versionné, pas un temporaire : le visualiseur affiche le
# chemin du fichier chargé en haut à droite, et « /tmp/tmpj4i41m45/… » dans
# une capture publiée fait négligé.
FAUTIF = Path(__file__).resolve().parent.parent / 'exemples' / 'arc_fautif.ngc'

# Le perçage du lit, copie forcée en mode coupe. L'original est livré en essai
# à blanc et ne creuse RIEN : la capture de matière y montrait une planche
# intacte. Six poches de Ø30 dans un bloc, c'est le sujet qui montre le mieux
# le bois s'enlever — `paquerette2.ngc`, gravure large et peu profonde sur
# 585 × 1008 mm, ne laissait rien voir du relief à cette échelle.
COUPE = Path(__file__).resolve().parent.parent / 'exemples' / 'percage_lit_coupe.ngc'


def capturer(nom: str, fichier: Path, *options: str) -> bool:
    """Lance capturer.py une fois. Rend True si l'image est bien écrite."""
    cible = SORTIE / nom
    avant = cible.stat().st_mtime if cible.exists() else 0

    cmd = [sys.executable, 'outils/capturer.py', str(fichier), str(cible),
           *options]
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    r = subprocess.run(cmd, cwd=PROJET, env=env,
                       capture_output=True, text=True, timeout=600)

    if not cible.exists() or cible.stat().st_mtime <= avant:
        print(f"  ÉCHEC  {nom}")
        for ligne in (r.stderr or r.stdout).splitlines()[-6:]:
            print(f"         {ligne}")
        return False

    note = '' if r.returncode == 0 else '  (core dump au démontage, image OK)'
    print(f"  {nom:<30} {cible.stat().st_size // 1024:>4} Ko{note}")
    return True


def main() -> None:
    if not PROJET.is_dir():
        sys.exit(f"capturer_visualiseur : projet introuvable ({PROJET})")

    manquants = [f for f in (PERCAGE, PAQUERETTE) if not f.exists()]
    if manquants:
        print("  ! fichiers G-code absents : "
              + ', '.join(f.name for f in manquants))

    SORTIE.mkdir(parents=True, exist_ok=True)
    ok = 0

    if PERCAGE.exists():
        # Le fichier paramétré qui est à l'origine du projet, en iso.
        ok += capturer('visualiseur-percage.png', PERCAGE,
                       '--vue', 'iso', '--mode', '0')

    if PAQUERETTE.exists():
        # Le gros fichier — 561 931 segments — coloré par profondeur Z.
        ok += capturer('visualiseur-paquerette.png', PAQUERETTE,
                       '--vue', 'dessus', '--mode', '1')

    # Le bloc de bois creusé, à mi-parcours pour qu'on voie le relief se
    # former plutôt qu'une pièce déjà finie : à 55 %, la dernière poche n'est
    # pas encore entamée.
    if COUPE.exists():
        ok += capturer('visualiseur-matiere.png', COUPE,
                       '--vue', 'iso', '--mode', '0',
                       '--matiere', '6.0', '--avancement', '0.55')
    else:
        print(f"  ! fixture absente : {COUPE}")

    # Le bandeau d'erreur, sur le fichier fautif du dépôt.
    if FAUTIF.exists():
        ok += capturer('visualiseur-erreur.png', FAUTIF,
                       '--vue', 'dessus', '--mode', '0')
    else:
        print(f"  ! fixture absente : {FAUTIF}")

    print(f"\n{ok} capture(s) écrite(s) dans {SORTIE}")
    if not ok:
        sys.exit("aucune capture — rs274 répond-il ? (essayer « rs274 -g » "
                 "sur un fichier simple)")


if __name__ == '__main__':
    main()
