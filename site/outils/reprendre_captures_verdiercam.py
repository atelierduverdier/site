#!/usr/bin/env python3
# =========================================================================
# reprendre_captures_verdiercam.py — les images de la fiche VerdierCAM
# =========================================================================
# Les captures ne se font PAS ici. Elles se font dans le dépôt de la
# présentation (realisations/presentation-verdiercam/capturer.sh), qui
# rejoue des scénarios dans le vrai logiciel, sur un profil jetable, avec un
# repère G54 importé pour que l'avertissement « décalage inconnu » ne salisse
# pas les vues 3D. Ce script ne fait que les REPRENDRE :
#
#   * les PNG 2880 × 1620 sont ramenés à 1920 de large — au-delà, le texte
#     de l'interface ne gagne rien à l'écran et le dépôt du site s'alourdit ;
#   * les clips MP4 sont recopiés tels quels, avec leur première image en
#     PNG pour servir d'affiche (`poster`) avant la lecture.
#
# Tout part dans site/contenu/captures/verdiercam-*.{png,mp4} ; generer.py
# les passe en WebP et les nomme par empreinte, comme les autres.
#
# Après une nouvelle version : relancer capturer.sh là-bas, puis ce script.
#
# UTILISATION :
#   python3 site/outils/reprendre_captures_verdiercam.py
# =========================================================================

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chemins  # noqa: E402

SOURCE = chemins.VERDIERCAM_PRESENTATION
CIBLE = Path(__file__).resolve().parent.parent / 'contenu' / 'captures'
LARGEUR = 1920

# nom dans la présentation -> nom sur le site (sans extension)
IMAGES = {
    'assiette_bois': 'verdiercam-assiette',
    'assiette_decoree_bois': 'verdiercam-assiette-decoree',
    'boite_couvercle_bois': 'verdiercam-boite',
    'cadre_parcours': 'verdiercam-cadre-parcours',
    'croquis_contraint': 'verdiercam-croquis',
    'levier_croquis': 'verdiercam-levier',
    'accueil_trois_modes': 'verdiercam-trois-modes',
    'debutant_profondeurs': 'verdiercam-debutant-profondeurs',
    'debutant_vcarve': 'verdiercam-debutant-vcarve',
    'gravure25d_schema': 'verdiercam-25d-schema',
    'gravure25d_bois': 'verdiercam-25d-bois',
    'pilotage_pupitre': 'verdiercam-pupitre',
}

# Le héros : la fenêtre entière n'y fait que 500 px de large, l'interface y
# devient une bouillie grise. On n'en garde que la vue 3D — la pièce dans le
# bois, qui se lit à toute taille. Boîte en pixels de la capture 2880 × 1620.
RECADRES = {
    'verdiercam-heros': ('assiette_bois', (880, 360, 2200, 1240)),
}

CLIPS = {
    'croquis_cote_tapee': 'verdiercam-clip-cote',
    'debutant_profondeurs_reglage': 'verdiercam-clip-debutant',
    'simulation_creuse': 'verdiercam-clip-simulation',
}


def main() -> None:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("il faut Pillow")
    CIBLE.mkdir(parents=True, exist_ok=True)
    manquants = []

    for src, dst in IMAGES.items():
        f = SOURCE / 'captures' / f'{src}.png'
        if not f.is_file():
            manquants.append(f)
            continue
        im = Image.open(f).convert('RGB')
        if im.width > LARGEUR:
            im = im.resize((LARGEUR, round(im.height * LARGEUR / im.width)),
                           Image.LANCZOS)
        im.save(CIBLE / f'{dst}.png', optimize=True)
        print(f"  {dst}.png  {im.width}×{im.height}")

    for dst, (src, boite) in RECADRES.items():
        f = SOURCE / 'captures' / f'{src}.png'
        if not f.is_file():
            manquants.append(f)
            continue
        im = Image.open(f).convert('RGB').crop(boite)
        im.save(CIBLE / f'{dst}.png', optimize=True)
        print(f"  {dst}.png  {im.width}×{im.height} (recadré)")

    for src, dst in CLIPS.items():
        video = SOURCE / 'clips' / f'{src}.mp4'
        affiche = SOURCE / 'clips' / f'{src}.png'
        if not video.is_file() or not affiche.is_file():
            manquants.append(video)
            continue
        shutil.copy2(video, CIBLE / f'{dst}.mp4')
        Image.open(affiche).convert('RGB').save(CIBLE / f'{dst}.png', optimize=True)
        print(f"  {dst}.mp4  {video.stat().st_size // 1024} Ko (+ affiche)")

    if manquants:
        sys.exit("absents : " + ', '.join(str(m) for m in manquants))


if __name__ == '__main__':
    main()
