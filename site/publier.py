#!/usr/bin/env python3
# =========================================================================
# publier.py — régénère le site et le pousse sur la branche gh-pages
# =========================================================================
# GitHub Pages sert la branche `gh-pages` du dépôt. Or site/public/ est
# IGNORÉ par git (reconstruit à chaque génération, rien à versionner) :
# on ne peut donc pas servir un sous-dossier de main. Ce script fait le
# pont, à la main et sans CI — le style de la maison :
#
#   1. régénère public/ par generer.py (qui s'arrête net si une clé
#      manque au modèle — rien d'à moitié généré ne part en ligne) ;
#   2. fabrique dans public/ un dépôt jetable d'un seul commit ;
#   3. le pousse de force sur gh-pages.
#
# L'historique de gh-pages n'a aucune valeur : c'est un produit, main
# porte la vraie histoire. Le force-push est donc le comportement voulu.
#
# UTILISATION :
#   python3 site/publier.py            # régénère + pousse
#   python3 site/publier.py --sec      # régénère seulement, ne pousse pas
# =========================================================================

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / 'site' / 'public'
BRANCHE = 'gh-pages'


def courir(cmd, **kw):
    r = subprocess.run(cmd, cwd=kw.pop('cwd', RACINE), text=True,
                       capture_output=True, **kw)
    if r.returncode != 0:
        sys.exit(f"publier : échec de {' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def main() -> None:
    # 0. Les planches reprises des projets sont-elles à jour ? Ce sont des
    #    artefacts tirés d'autres artefacts — modèle → PDF → PNG → WebP —
    #    et rien dans la chaîne ne garantit l'ordre des dates. Le 12/08/2026,
    #    une planche corrigée à 20 h 27 s'est affichée en ligne dans sa
    #    version de 20 h 02 : le dessin existait, il était simplement
    #    d'avant, et ça ne se voyait qu'en ouvrant le PDF à côté.
    print("--- fraîcheur des planches reprises ---")
    r = subprocess.run([sys.executable,
                        str(RACINE / 'site' / 'outils' / 'reprendre_plans.py'),
                        '--verifier'], cwd=RACINE)
    if r.returncode != 0:
        sys.exit("publier : une planche du site est plus vieille que sa "
                 "source — rien n'est poussé.\n"
                 "  python3 site/outils/reprendre_plans.py")

    # 1. Régénérer. Le générateur porte les garde-fous ; on ne les répète pas.
    r = subprocess.run([sys.executable, str(RACINE / 'site' / 'generer.py')],
                       cwd=RACINE)
    if r.returncode != 0:
        sys.exit("publier : la génération a échoué — rien n'est poussé.")

    if '--sec' in sys.argv:
        print("(--sec : génération seule, rien n'est poussé)")
        return

    distant = courir(['git', 'remote', 'get-url', 'origin'])

    # 2. Un dépôt jetable dans public/, un seul commit.
    git_jetable = PUBLIC / '.git'
    if git_jetable.exists():
        courir(['rm', '-rf', str(git_jetable)])
    courir(['git', 'init', '-q', '-b', BRANCHE], cwd=PUBLIC)
    courir(['git', 'add', '-A'], cwd=PUBLIC)
    version = courir(['git', 'rev-parse', '--short', 'HEAD'])
    courir(['git', 'commit', '-q', '-m',
            f"Site engendré depuis {version} — ne pas éditer ici"], cwd=PUBLIC)

    # 3. Pousser. --force : gh-pages est un produit, pas une histoire.
    courir(['git', 'push', '--force', distant, f'{BRANCHE}:{BRANCHE}'],
           cwd=PUBLIC)
    courir(['rm', '-rf', str(git_jetable)])

    print(f"poussé sur {BRANCHE} (engendré depuis {version})")


if __name__ == '__main__':
    main()
