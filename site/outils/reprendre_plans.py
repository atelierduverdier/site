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
# LA FRAÎCHEUR SE VÉRIFIE, ELLE NE SE SUPPOSE PAS. Cette image est un
# artefact tiré d'un autre artefact : modèle FreeCAD → PDF → PNG → WebP →
# site. Chaque maillon porte sa date, et c'est LA PLUS ANCIENNE qui décide
# de ce qu'on voit. Le 12/08/2026, la planche de la tonnelle a été corrigée
# à 20 h 27 ; son image datait de 20 h 02, et le site a montré pendant des
# heures une perspective posée en travers de l'élévation de côté. Rien ne
# l'a signalé — l'image existait, elle était simplement d'avant.
#
# D'où `--verifier`, que `publier.py` appelle : si une image est plus vieille
# que son PDF, la publication s'arrête. Mieux vaut ne rien publier qu'un
# dessin périmé, qu'on croit juste parce qu'il s'affiche.
#
# UTILISATION :
#   python3 site/outils/reprendre_plans.py             # reprend les planches
#   python3 site/outils/reprendre_plans.py --verifier  # contrôle seul, ne rend rien
# =========================================================================

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chemins

RACINE = Path(__file__).resolve().parent.parent.parent
SORTIE = RACINE / 'site' / 'contenu' / 'captures'
RESOLUTION = 150          # dpi ; au-delà le WebP grossit sans gagner en lisibilité

# (nom sur le site, source, page, ce que l'image montre)
#
# `page` à None = la source est DÉJÀ une image, on la recopie. La dust shoe
# a son propre studio de rendu (Blender, `outils/rendu.sh` de son dépôt) :
# refaire un rendu ici serait une seconde vérité à tenir à jour, exactement
# ce que l'en-tête de ce fichier refuse. Ces PNG-là ne sont pas versionnés
# (`rendu/` est ignoré chez eux) — d'où le contrôle de fraîcheur, qui dira
# « source introuvable » plutôt que de publier l'image d'avant.
PLANCHES = [
    ('plan-meuble-ensemble',
     Path.home() / 'Projets' / 'realisations' / 'meuble-balais' / 'Plan_Ensemble.pdf',
     1, "élévations, dessus, perspective et tableau des cotes"),
    ('plan-tonnelle-ensemble',
     Path.home() / 'Projets' / 'realisations' / 'tonnelle-jasmin' / 'docs' / 'plans.pdf',
     1, "élévation de face, vue de dessus, côté et perspective"),
    # La dust shoe sort CINQ planches ; on en reprend deux — celle qui
    # raconte le montage, et celle de la pièce qui explique tout le reste.
    # Le chemin passe par `chemins.py` : c'est le seul endroit où il vit.
    ('plan-dust-shoe-ensemble',
     chemins.DUST_SHOE_PLANS / '05-ensemble.pdf',
     1, "les deux montages, la perspective et la nomenclature"),
    ('plan-dust-shoe-adaptateur',
     chemins.DUST_SHOE_PLANS / '03-adaptateur.pdf',
     1, "l'adaptateur : tenon en T, conduit en D, pied à cordon"),
    ('vue3d-dust-shoe-fraisage',
     chemins.DUST_SHOE / 'rendu' / 'fraisage.png',
     None, "en fraisage : semelle, brosse et adaptateur en place"),
    ('vue3d-dust-shoe-parque',
     chemins.DUST_SHOE / 'rendu' / 'parque.png',
     None, "au parcage : la brosse seule reste dans le quai"),
    # Le film du parcage, deux prises. Il ne se convertit pas — il se
    # recopie —, mais il passe par le même contrôle de fraîcheur : une
    # vidéo périmée ment exactement comme un dessin périmé.
    ('video-dust-shoe-parcage-1',
     chemins.DUST_SHOE / 'rendu' / 'parcage-1.mp4',
     None, "le parcage en quatre temps, prise large"),
    ('video-dust-shoe-parcage-2',
     chemins.DUST_SHOE / 'rendu' / 'parcage-2.mp4',
     None, "le même, cadré serré"),
]


def _cible(nom: str, source: Path, page) -> Path:
    """Le fichier produit dans contenu/captures/.

    Un PDF devient un PNG ; une source déjà en image — ou en vidéo —
    garde son extension.
    """
    return SORTIE / (nom + ('.png' if page else source.suffix))


def _horodate(chemin: Path) -> str:
    return datetime.fromtimestamp(chemin.stat().st_mtime).strftime('%d/%m %H:%M')


def perimees() -> list[str]:
    """Les images du site qui ne disent plus ce que dit leur PDF.

    Une image ABSENTE ou plus VIEILLE que sa source est un souci ; une source
    absente aussi, et c'en était un silencieux : la boucle se contentait d'un
    « ! absent » et le script sortait quand même en 0.
    """
    soucis = []
    for nom, pdf, page, _quoi in PLANCHES:
        image = _cible(nom, pdf, page)
        if not pdf.exists():
            soucis.append(f"{nom} : la source est introuvable — {pdf}")
        elif not image.exists():
            soucis.append(f"{nom} : aucune image reprise — lancer "
                          f"reprendre_plans.py")
        elif image.stat().st_mtime < pdf.stat().st_mtime:
            soucis.append(
                f"{nom} : l'image date du {_horodate(image)}, la planche du "
                f"{_horodate(pdf)} — le site montrerait un dessin d'avant. "
                f"Lancer reprendre_plans.py.")
    return soucis


def verifier() -> int:
    soucis = perimees()
    for s in soucis:
        print(f"  ✗ {s}")
    if not soucis:
        print(f"  {len(PLANCHES)} planche(s) à jour.")
    return 1 if soucis else 0


def main() -> None:
    if '--verifier' in sys.argv:
        sys.exit(verifier())

    if not subprocess.run(['which', 'pdftoppm'], capture_output=True).returncode == 0:
        sys.exit("reprendre_plans : il faut pdftoppm (paquet poppler).")

    SORTIE.mkdir(parents=True, exist_ok=True)
    total = 0
    for nom, pdf, page, quoi in PLANCHES:
        if not pdf.exists():
            # Une source absente ne se contourne pas : sans elle, l'image
            # gardée est celle d'avant, et personne ne le verra.
            sys.exit(f"reprendre_plans : source introuvable — {pdf}")

        cible = _cible(nom, pdf, page)
        if page is None:
            shutil.copy2(pdf, cible)
            total += cible.stat().st_size
            print(f"  {cible.name:<30} {cible.stat().st_size // 1024:>5} Ko   {quoi}")
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
        produits[0].replace(cible)
        for reste in produits[1:]:
            reste.unlink()

        total += cible.stat().st_size
        print(f"  {cible.name:<30} {cible.stat().st_size // 1024:>5} Ko   {quoi}")

    print(f"\n{len(PLANCHES)} image(s), {total // 1024} Ko en PNG "
          f"(generer.py les passera en WebP)")


if __name__ == '__main__':
    main()
