#!/usr/bin/env python3
# =========================================================================
# capturer_coupe.py — copie d'écran de l'appli « vitesses de coupe »
# =========================================================================
# Rend site/appli/coupe/index.html HORS ÉCRAN dans un QWebEngineView, à
# l'échelle 2 pour une image nette, et grabbe le haut de l'appli — les
# matières et la carte des résultats. Le PNG part dans
# site/contenu/captures/appli-coupe.png ; generer.py le convertit en WebP
# pour la fiche et en fait la carte de partage.
#
# Aucune dépendance au serveur : la page est chargée en file://, elle est
# autonome (le service worker et le compteur échouent en silence, sans
# écran ni réseau, et l'appli n'en a pas besoin pour calculer).
#
# UTILISATION :
#   python3 site/outils/capturer_coupe.py
# =========================================================================

import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
# On capture l'appli TELLE QU'ELLE EST PUBLIÉE, pas la source : c'est
# generer.py qui y pose le logo de la maison, la source ne porte qu'une
# marque. Lancer `python3 site/generer.py` d'abord.
APPLI = RACINE / 'public' / 'coupe' / 'index.html'
SORTIE = RACINE / 'contenu' / 'captures' / 'appli-coupe.png'

# Échelle 2 : la page fait 460 px de large au plus, on la rend à 920 pour
# que le texte de 11 px reste net une fois en WebP.
ECHELLE = 2
# Vue BUREAU depuis la refonte v16 : c'est en deux colonnes que l'appli se
# comprend d'un coup d'œil — le résultat à droite pendant qu'on règle à
# gauche. Sous 900 px elle repasse en une colonne, mais ce n'est pas cette
# vue-là qui explique le mieux ce qu'elle fait.
LARGEUR = 1180
# Jusqu'au bas de la carte des résultats, ALERTE COMPRISE : avec les réglages
# par défaut (Ø6, plafond 1 500) l'appli avertit que l'avance dépasse ce que
# la machine tient — c'est le garde-fou qui la distingue, il doit se voir.
HAUTEUR = 900


def _rogner_marges(image):
    """Enlève les bordures d'une seule couleur autour de l'image.

    Le fond de l'appli est uni (#09090b) : les marges gauche/droite du
    QWebEngineView (la page est centrée) et le vide sous le contenu se
    coupent proprement, sans nombre magique à régler à la main.
    """
    from PySide6.QtGui import qRgb
    coin = image.pixel(0, 0)
    w, h = image.width(), image.height()

    def ligne_unie(y):
        return all(image.pixel(x, y) == coin for x in range(0, w, 3))

    def colonne_unie(x):
        return all(image.pixel(x, y) == coin for y in range(0, h, 3))

    haut = 0
    while haut < h - 1 and ligne_unie(haut):
        haut += 1
    bas = h - 1
    while bas > haut and ligne_unie(bas):
        bas -= 1
    gauche = 0
    while gauche < w - 1 and colonne_unie(gauche):
        gauche += 1
    droite = w - 1
    while droite > gauche and colonne_unie(droite):
        droite -= 1

    # Une marge d'air égale tout autour, dans la teinte du fond.
    marge = 12 * ECHELLE
    gauche = max(0, gauche - marge)
    droite = min(w - 1, droite + marge)
    haut = max(0, haut - marge)
    bas = min(h - 1, bas + marge)
    return image.copy(gauche, haut, droite - gauche + 1, bas - haut + 1)


def main() -> None:
    if not APPLI.exists():
        sys.exit(f"capturer_coupe : appli introuvable ({APPLI}).\n"
                 f"  Lancer d'abord : python3 site/generer.py")

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS',
                          '--disable-gpu --no-sandbox --disable-dev-shm-usage')
    os.environ['QT_SCALE_FACTOR'] = str(ECHELLE)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtCore import QUrl, QTimer, QEventLoop

    app = QApplication(sys.argv)
    vue = QWebEngineView()
    vue.resize(LARGEUR, HAUTEUR)
    vue.setUrl(QUrl.fromLocalFile(str(APPLI)))
    vue.show()

    # Attendre le chargement, puis laisser le script peindre les boutons
    # matières et calculer les résultats avant de grabber.
    boucle = QEventLoop()
    etat = {'charge': False}

    def fini(ok):
        etat['charge'] = ok
        QTimer.singleShot(600, boucle.quit)

    vue.loadFinished.connect(fini)
    QTimer.singleShot(8000, boucle.quit)      # filet, ne pas rester bloqué
    boucle.exec()

    if not etat['charge']:
        sys.exit("capturer_coupe : la page ne s'est pas chargée.")

    # Masquer la barre de défilement : le QWebEngineView est plus court que
    # l'appli entière, sinon une barre grise traîne sur le bord droit et le
    # rognage s'arrête dessus au lieu de couper au fond.
    masquer = QEventLoop()
    vue.page().runJavaScript(
        "var s=document.createElement('style');"
        "s.textContent='html{overflow:hidden!important}"
        "::-webkit-scrollbar{width:0!important;height:0!important;display:none!important}';"
        "document.head.appendChild(s);",
        lambda _res: QTimer.singleShot(120, masquer.quit))
    QTimer.singleShot(2000, masquer.quit)
    masquer.exec()

    app.processEvents()
    image = vue.grab().toImage()
    image = _rogner_marges(image)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(SORTIE)):
        sys.exit(f"capturer_coupe : échec de l'écriture de {SORTIE}")
    print(f"  {SORTIE.name:<20} {image.width()}×{image.height()}  "
          f"{SORTIE.stat().st_size // 1024} Ko")


if __name__ == '__main__':
    main()
