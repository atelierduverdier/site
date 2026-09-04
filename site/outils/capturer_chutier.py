#!/usr/bin/env python3
# =========================================================================
# capturer_chutier.py — copies d'écran du chutier, pour le site
# =========================================================================
# Lance l'interface HORS ÉCRAN, lui fait charger ses propres exemples, et
# grabbe la fenêtre. Les PNG partent dans site/contenu/captures/chutier-*.png
# et sont recopiés dans public/ par generer.py.
#
# QUATRE IMAGES, et chacune dit une chose que les autres ne disent pas :
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
#   chutier-formes.png      l'exemple des formes biscornues : l'imbrication
#                           CNC par no-fit polygon, un cadre évidé avec une
#                           pièce dedans, des équerres emboîtées.
#
# (chutier-web.png, la version dans le navigateur, est une capture de
# Chrome sur la page servie en local — pas une fenêtre Qt, ce script ne
# peut pas la faire.)
#
# HORS ÉCRAN via QT_QPA_PLATFORM=offscreen : rien n'apparaît sur le bureau.
#
# LES RÉGLAGES QT ET LE STOCK DE L'ATELIER SONT DÉTOURNÉS vers un dossier
# jetable, par XDG_CONFIG_HOME et CHUTIER_ATELIER — posés AVANT tout import
# Qt (QSettings.setPath ne détourne rien sur Linux, vu le 03/09/2026). Le
# chutier retient le trait de scie, la géométrie de sa fenêtre et le stock
# de l'atelier d'une séance à l'autre : sans ce détour, une capture écrirait
# dans la configuration de l'atelier, et surtout elle DÉPENDRAIT d'elle.
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
    jetable = tempfile.mkdtemp(prefix='chutier-captures-')
    os.environ['XDG_CONFIG_HOME'] = jetable
    os.environ['CHUTIER_ATELIER'] = os.path.join(jetable, 'atelier.json')
    # Pas de pastille verte ou orange au hasard du réseau sur une capture
    # publiée : elle changerait d'un tirage à l'autre.
    os.environ['CHUTIER_SANS_RESEAU'] = '1'
    sys.path.insert(0, str(PROJET))

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication

    import interface

    # Le calcul dans un fil ne rend pas la main avant le grab : la capture
    # montrait alors le plan de l'exemple PRÉCÉDENT sous la saisie du
    # nouveau (vu le 04/09/2026 sur chutier-formes.png, un débit de sapin
    # sous une table de formes biscornues). En synchrone, chaque
    # `_calculer()` est fini quand il rend la main.
    interface.SYNCHRONE = True

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

    # 2. L'exemple aux chutes : la table du stock (pièces et stock sont
    #    l'un sous l'autre depuis le 03/09/2026) avec ses colonnes Chute et
    #    Atelier, sa colonne Défauts, et sur le plan la chute d'étagère
    #    entamée avant tout bois neuf, son nœud écarté hachuré. Le nom de
    #    projet posé juste avant est REPRIS : sans ce retour à zéro, la
    #    barre d'état annonçait « Volets battants.json » sous un débit de
    #    panneaux.
    fenetre._chemin = None
    fenetre._modifie = False
    fenetre._charger_exemple()
    fenetre._calculer()
    # Douze colonnes de stock : on donne sa place à la saisie pour cette
    # image-là, c'est elle qu'on vient y lire.
    fenetre._splitter.setSizes([760, FENETRE[0] - 760])
    app.processEvents()
    ecrire('chutier-chutes.png', fenetre.grab())

    # 4. Les formes biscornues, imbriquées à la fraise — la chute seule,
    #    en grand : c'est là que le cadre évidé reçoit un cœur et que les
    #    équerres s'emboîtent ; empilée sous le panneau de 1200 × 600 elle
    #    tenait dans un timbre-poste.
    fenetre._modifie = False
    fenetre._charger_exemple_formes()
    fenetre._calculer()
    fenetre._splitter.setSizes([560, FENETRE[0] - 560])
    fenetre.choix_vue.setCurrentIndex(1)
    fenetre.liste_planches.setCurrentRow(0)
    app.processEvents()
    ecrire('chutier-formes.png', fenetre.grab())


if __name__ == '__main__':
    main()
