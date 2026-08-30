#!/usr/bin/env python3
# =========================================================================
# capturer_chutier.py — copies d'écran du chutier, pour le site
# =========================================================================
# Lance l'interface HORS ÉCRAN, lui fait charger ses propres exemples, et
# grabbe la fenêtre. Les PNG partent dans site/contenu/captures/chutier-*.png
# et sont recopiés dans public/ par generer.py.
#
# TROIS IMAGES, et chacune dit une chose que les autres ne disent pas :
#
#   chutier-plan.png        le débit RÉEL d'une paire de volets battants —
#                           l'exemple que porte l'appli, tiré du modèle
#                           FreeCAD du projet. Cinq brins de douglas, seize
#                           pièces, le plan entier d'un coup d'œil.
#   chutier-chutes.png      l'exemple « panneaux », le seul des deux dont le
#                           stock porte des CHUTES. C'est la raison d'être du
#                           programme : la planche 3 du plan est une chute
#                           d'étagère qu'on écoule avant d'entamer du neuf.
#   chutier-impression.png  la page qu'on emporte à l'établi. Elle n'est pas
#                           une capture de fenêtre : elle est peinte par
#                           _dessiner_page sur une image aux dimensions
#                           d'une A4 paysage, exactement comme sur papier.
#
# HORS ÉCRAN via QT_QPA_PLATFORM=offscreen : rien n'apparaît sur le bureau.
#
# LES RÉGLAGES QT SONT DÉTOURNÉS vers un dossier jetable. Le chutier retient
# le trait de scie et la géométrie de sa fenêtre d'une séance à l'autre :
# sans ce détour, une capture écrirait dans la configuration de l'atelier,
# et surtout elle DÉPENDRAIT d'elle — la même commande ne rendrait pas la
# même image selon ce qui traîne dans ~/.config.
#
# UTILISATION :
#   python3 site/outils/capturer_chutier.py
# =========================================================================

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chemins

PROJET = chemins.CHUTIER
SORTIE = Path(__file__).resolve().parent.parent / 'contenu' / 'captures'

FENETRE = (1560, 900)
# A4 paysage à 150 points par pouce : la page telle qu'elle sort.
PAGE = (1754, 1240)


def main() -> None:
    if not PROJET.is_dir():
        sys.exit(f"capturer_chutier : projet introuvable ({PROJET})")

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    sys.path.insert(0, str(PROJET))

    from PySide6.QtCore import QRectF, QSettings, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication

    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                      tempfile.mkdtemp(prefix='chutier-captures-'))

    import interface

    app = QApplication(sys.argv)
    fenetre = interface.FenetrePrincipale()
    fenetre.resize(*FENETRE)
    fenetre.show()
    app.processEvents()

    SORTIE.mkdir(parents=True, exist_ok=True)

    def ecrire(nom: str, image) -> None:
        cible = SORTIE / nom
        if not image.save(str(cible)):
            sys.exit(f"capturer_chutier : échec de l'écriture de {cible}")
        print(f"  {nom:<28} {image.width()}×{image.height()}  "
              f"{cible.stat().st_size // 1024} Ko")

    # 1. Le débit des volets, plan entier.
    fenetre._charger_exemple_volets()
    app.processEvents()
    ecrire('chutier-plan.png', fenetre.grab())

    # 3. La page imprimée du MÊME débit — avant de changer d'exemple.
    #    Le titre de la page reprend le nom du fichier de projet ; on lui
    #    en donne un plutôt que de publier « Feuille de débit ».
    fenetre._chemin = str(Path.home() / 'Volets battants.json')
    page = QImage(*PAGE, QImage.Format.Format_ARGB32)
    page.fill(Qt.GlobalColor.white)
    peintre = QPainter(page)
    try:
        planches = fenetre.vue.debits_affiches()
        fenetre._dessiner_page(peintre, fenetre._image_du_plan(planches, 1700),
                               1, 1, planches)
    finally:
        peintre.end()
    ecrire('chutier-impression.png', page)

    # 2. L'exemple aux chutes, onglet Stock : on y voit la colonne cochée,
    #    et sur le plan la chute d'étagère entamée avant tout bois neuf.
    #    Le nom de projet posé juste avant est REPRIS : sans ce retour à
    #    zéro, la barre d'état annonçait « Volets battants.json » sous un
    #    débit de panneaux.
    fenetre._chemin = None
    fenetre._modifie = False
    fenetre._charger_exemple()
    fenetre.onglets_saisie.setCurrentIndex(1)
    # Le stock porte dix colonnes ; à la largeur d'usage la première, qui
    # s'étire, ne gardait plus que « sapin … ». On donne sa place à la
    # saisie pour cette image-là : c'est elle qu'on vient y lire.
    fenetre._splitter.setSizes([760, FENETRE[0] - 760])
    app.processEvents()
    ecrire('chutier-chutes.png', fenetre.grab())


if __name__ == '__main__':
    main()
