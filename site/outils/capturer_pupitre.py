#!/usr/bin/env python3
# =========================================================================
# capturer_pupitre.py — copies d'écran du pupitre Graphtec, pour le site
# =========================================================================
# Lance `pupitre.py` HORS ÉCRAN, lui fait ouvrir un SVG d'exemple, et grabbe
# chacun de ses trois onglets. Les PNG partent dans
# site/contenu/captures/pupitre-*.png et sont recopiés dans public/ par
# generer.py.
#
# CE SCRIPT NE PARLE JAMAIS À LA MACHINE. Il ne touche à aucun bouton qui
# ouvre /dev/usb/lp0 : ni « Interroger le média », ni « Lire la machine »,
# ni « Envoyer ». Il refuse même de démarrer si le traceur est branché —
# une capture ne vaut pas le risque de faire bouger une plume sur du papier.
#
# HORS ÉCRAN via QT_QPA_PLATFORM=offscreen : rien n'apparaît sur le bureau,
# et aucun serveur X supplémentaire n'est nécessaire.
#
# UTILISATION :
#   python3 site/outils/capturer_pupitre.py
# =========================================================================

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chemins

PROJET = chemins.GRAPHTEC
SORTIE = Path(__file__).resolve().parent.parent / 'contenu' / 'captures'

# Le dessin montré dans les captures. Un gabarit technique disait mal ce que
# fait la machine ; celui-ci se lit d'un coup d'œil.
EXEMPLE = (Path.home() / 'Téléchargements' / 'Creative Fabrica'
           / 'Funny-Birds-Branch-SVG-Laser-154323584'
           / 'Funny  Birds Branch SVG Laser Cut .svg')

# Les trois onglets, dans l'ordre où le pupitre les présente.
ONGLETS = [
    (0, 'pupitre-dessin.png'),
    (1, 'pupitre-outil.png'),
    (2, 'pupitre-machine.png'),
]


def garde_fou() -> None:
    """Refuse de tourner si le traceur est joignable."""
    for peripherique in Path('/dev/usb').glob('lp*') if Path('/dev/usb').is_dir() else []:
        sys.exit(f"capturer_pupitre : {peripherique} existe — le traceur est branché.\n"
                 f"Débranche-le avant de capturer : aucune image ne vaut le risque\n"
                 f"de faire bouger une plume sur du papier.")


def main() -> None:
    garde_fou()

    if not PROJET.is_dir():
        sys.exit(f"capturer_pupitre : projet introuvable ({PROJET})")

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    sys.path.insert(0, str(PROJET))
    os.chdir(PROJET)                      # le pupitre lit des chemins relatifs

    from PySide6.QtWidgets import QApplication
    import pupitre

    app = QApplication(sys.argv)
    fenetre = pupitre.Pupitre()
    fenetre.resize(1060, 660)

    # Ouvrir le SVG SANS passer par la boîte de dialogue : on reproduit ce
    # que fait _ouvrir(), sans l'interaction.
    if EXEMPLE.exists():
        brut, avertissements = pupitre.noyau.charger(str(EXEMPLE))
        if brut:
            fenetre.brut = brut
            fenetre.chemin = str(EXEMPLE)
            fenetre.lbl_fichier.setText(EXEMPLE.name)
            fenetre.b_envoyer.setEnabled(True)
            fenetre.apercu.reinitialiser_vue()
            fenetre._recalculer()
            # « Ajuster au média » : sans lui, le gabarit d'exemple fait
            # 600 × 130 mm sur un média de 380 × 285, et la capture s'ouvre
            # sur un bandeau rouge « LE DESSIN DÉBORDE DE LA ZONE UTILE ».
            # C'est un état d'erreur légitime, mais ce n'est pas ce qu'une
            # page d'accueil doit montrer en premier.
            fenetre._ajuster()
            app.processEvents()
            print(f"  SVG chargé et ajusté : {EXEMPLE.name}")
        else:
            print(f"  ! {EXEMPLE.name} n'a rien de traçable — capture sans dessin")
    else:
        print(f"  ! exemple absent ({EXEMPLE}) — capture sans dessin")

    fenetre.show()
    app.processEvents()

    SORTIE.mkdir(parents=True, exist_ok=True)
    for index, nom in ONGLETS:
        fenetre.onglets.setCurrentIndex(index)
        app.processEvents()
        image = fenetre.grab()
        cible = SORTIE / nom
        if not image.save(str(cible)):
            sys.exit(f"capturer_pupitre : échec de l'écriture de {cible}")
        print(f"  {nom:<26} {image.width()}×{image.height()}  "
              f"{cible.stat().st_size // 1024} Ko")


if __name__ == '__main__':
    main()
