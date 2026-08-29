#!/usr/bin/env python3
# =========================================================================
# generer.py — engendre le site atelierduverdier.fr
# =========================================================================
# Colle kit/entete.html + contenu/<page>.html + kit/pied.html, recopie le
# kit et les ressources, et écrit tout dans public/.
#
# UTILISATION :
#   python3 site/generer.py
#
# Le dossier public/ est ENTIÈREMENT reconstruit à chaque passage : ne rien
# y éditer à la main, tout part de contenu/ et de kit/.
# =========================================================================

import html
import re
import hashlib
import shutil
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chemins
import valeurs_atc
import valeurs_attache
import valeurs_fcstd

RACINE = Path(__file__).resolve().parent.parent
KIT = RACINE / 'kit'
SITE = RACINE / 'site'
CONTENU = SITE / 'contenu'
PUBLIC = SITE / 'public'
MODELES_3D = CONTENU / 'modeles'      # les .glb engendrés par outils/exporter_glb.py
VENDU = SITE / 'vendu'                # les bibliothèques tierces, servies d'ici

# Planches reprises TELLES QUELLES depuis les projets, pour être servies
# en fichier — pas en image. Elles ne sont PAS régénérées ici : le modèle
# FreeCAD en est la source. Un dossier par projet : un projet absent ne
# doit pas emporter les autres, ce que faisait le `return` d'avant.
PLANS_REPRIS = [
    (chemins.ATC_PLANS, ['07-ensemble-monte.svg',
                         '01-siege-billes.svg',
                         '08-gabarit-essai.svg']),
    # les cinq planches de la dust shoe, reliées : c'est ce qu'on imprime
    (chemins.DUST_SHOE_PLANS, ['dust-shoe-plans.pdf']),
    # Les volets : les CINQ PLANCHES EXPORTEES A LA MAIN par Christophe,
    # une par une, apres les avoir retouchees dans TechDraw. On ne publie
    # surtout pas le recueil PDF engendre par le lot : il est anterieur a
    # ces retouches, et c'est la version corrigee qui fait foi. Plus les
    # deux A4 d'atelier, qui ne se retouchent pas.
    # L'attache de descente : la planche couleur, et les trois pièces à
    # imprimer. Ce sont des fichiers qu'on emporte, pas des images.
    (chemins.ATTACHE_RENDU, ['planche_collier.pdf', 'planche_collier.png']),
    (chemins.ATTACHE_STL, ['corps.stl', 'bride.stl', 'cale_point_fixe.stl']),
    (chemins.VOLETS_PLANS, ['Planche1.svg', 'Planche2.svg', 'Planche3.svg',
                            'Planche4.svg', 'Planche5.svg',
                            'Fiche-debit.pdf',
                            'Feuille-de-suivi.pdf']),
]

FICHIERS_KIT = ['verdier.css', 'verdier.js', 'chapeau.svg', 'logo.svg']

# --- La carte de partage -------------------------------------------------
# 1200 x 630, le format que Facebook, LinkedIn et Mastodon attendent pour
# une grande vignette. En JPEG, et c'est le point : le robot de Facebook ne
# lit PAS le WebP, et tout le reste du site est en WebP.
PARTAGE_L, PARTAGE_H = 1200, 630
PARTAGE_FOND = (246, 247, 249)      # --bg-2 clair : les rendus 3D s'y fondent
PARTAGE_ENCRE = (35, 39, 46)        # --fg
PARTAGE_ORANGE = (172, 91, 0)       # --orange-encre : 4,61:1 sur PARTAGE_FOND.
                                    # L'orange de marque n'y donnait que 2,8 —
                                    # et c'est le texte que voit tout le monde,
                                    # puisque c'est la vignette d'un lien partagé.
PARTAGE_GRIS = (90, 98, 110)        # --fg-2
POLICE = '/usr/share/fonts/TTF/DejaVuSans%s.ttf'


LASER_CORE = chemins.LASER_CORE


def version_laser() -> str:
    """La version de LaserAtelier, LUE DANS SA SOURCE.

    `VERSION` de `laser_core.py` est la seule source de vérité — elle est
    affichée dans chaque panneau et estampillée en tête de chaque G-code
    produit. Cette ligne est restée 44 versions en retard dans un fichier
    qui la recopiait ; le site ne sera pas le suivant.
    """
    if not LASER_CORE.exists():
        sys.exit(f"generer : {LASER_CORE} introuvable — impossible de lire la "
                 f"version de LaserAtelier.")
    for ligne in LASER_CORE.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^VERSION\s*=\s*["\']([^"\']+)["\']', ligne)
        if m:
            return m.group(1)
    sys.exit(f"generer : aucune ligne VERSION dans {LASER_CORE.name}.")


def injecter_fcstd(corps: str, nom: str) -> str:
    """Remplace les {{fcstd:doc:cle}} par une cote lue DANS le document.

    `{{fcstd:tonnelle:Largeur hors-tout (X)}}`  -> par libellé
    `{{fcstd:meuble:@Hauteur}}`                 -> par alias (le @ le dit)
    `{{fcstd:tonnelle:Poteau (carré)|1}}`       -> avec 1 décimale

    Les cotes de ces deux projets vivent dans le tableur de leur .FCStd,
    pas dans leur Python : celui-ci ne porte que des valeurs de départ.
    valeurs_fcstd s'arrête si le libellé manque ou si la cellule contient
    une formule — jamais de chiffre deviné.
    """
    if '{{fcstd:' not in corps:
        return corps

    docs = {
        'tonnelle': chemins.TONNELLE_FCSTD,
        'meuble': chemins.MEUBLE_FCSTD,
        # La dust shoe a DEUX modèles (un Part scripté qui fait référence,
        # un PartDesign d'où sortent les STL) et un seul tableur : c'est lui
        # qui les pilote, donc c'est lui qu'on lit.
        'dustshoe': chemins.DUST_SHOE_PARAMS,
        'dustshoe1': chemins.DUST_SHOE_PARAMS_V1,
        'volets': chemins.VOLETS_FCSTD,
    }

    def remplacer(m):
        doc, cle, dec = m.group(1), m.group(2), m.group(3)
        if doc not in docs:
            sys.exit(f"{nom} : document « {doc} » inconnu de injecter_fcstd.")
        d = int(dec) if dec else 0
        if cle.startswith('@'):
            return valeurs_fcstd.par_alias(docs[doc], cle[1:], d)
        return valeurs_fcstd.nombre(docs[doc], cle, d)

    corps = re.sub(r'\{\{fcstd:(\w+):([^|}]+?)(?:\|(\d+))?\}\}', remplacer, corps)
    reste = re.findall(r'\{\{fcstd:[^}]*\}\}', corps)
    if reste:
        sys.exit(f"{nom} : marque fcstd non résolue : {reste[0]}")
    return corps


def injecter_laser(corps: str, nom: str) -> str:
    """Remplace les {{laser.xxx}}. Une clé inconnue arrête la génération."""
    if '{{laser' not in corps:
        return corps
    connues = {'version': version_laser()}
    manquantes = []

    def remplacer(m):
        cle = m.group(1)
        if cle not in connues:
            manquantes.append(cle)
            return m.group(0)
        return connues[cle]

    corps = re.sub(r'\{\{laser\.(\w+)\}\}', remplacer, corps)
    if manquantes:
        sys.exit(f"{nom} : clé(s) laser inconnue(s) : "
                 f"{', '.join(sorted(set(manquantes)))}")
    return corps


# L'appli « vitesses de coupe », servie TELLE QUELLE sur /coupe/.
APPLI_COUPE = SITE / 'appli' / 'coupe'

# Ce que voit un réseau social qui partage l'appli. Titre, description et
# sous-titre de sa carte 1200x630 — voir partage_appli_coupe().
COUPE_TITRE = "Vitesses de coupe"
COUPE_DESCRIPTION = ("Calculateur d'avances et de vitesses pour le fraisage CNC : "
                     "neuf matières du sapin à l'acier doux, bibliothèque d'outils, "
                     "export FreeCAD. Installable, hors-ligne, rien n'est envoyé.")
COUPE_RESUME = ("Choisir broche et avance au pied de la fraiseuse — "
                "neuf matières, hors-ligne.")


def matieres_coupe() -> list:
    """Lit les matières DANS le code de l'appli — jamais recopiées.

    Le tableau de la fiche sort du même `MAT` que les boutons de l'appli :
    une valeur retouchée dans l'appli met la fiche à jour à la génération
    suivante. C'est la règle VERSION, appliquée aux vitesses de coupe.
    """
    source = APPLI_COUPE / 'index.html'
    if not source.exists():
        sys.exit(f"generer : {source} introuvable — l'appli fait partie du site.")
    texte = source.read_text(encoding='utf-8')
    bloc = re.search(r'var MAT = \{(.*?)\n\};', texte, re.S)
    if not bloc:
        sys.exit("generer : bloc « var MAT = {...}; » introuvable dans l'appli coupe.")
    motif = (r'\{label:"([^"]+)",\s*vcNum:(null|[\d.]+),\s*fzPerMm:([\d.]+),'
             r'\s*mode:"(rpm|vc)",\s*apLow:([\d.]+),\s*apHigh:([\d.]+),'
             r'\s*note:"([^"]*)"\}')
    matieres = [
        {'label': label,
         'vc': None if vc == 'null' else float(vc),
         'fz_par_mm': float(fz), 'mode': mode,
         'ap_lo': float(ap_lo), 'ap_hi': float(ap_hi), 'note': note}
        for label, vc, fz, mode, ap_lo, ap_hi, note
        in re.findall(motif, bloc.group(1))
    ]
    if not matieres:
        sys.exit("generer : aucune matière lue dans l'appli coupe — le motif "
                 "ne colle plus à l'écriture de MAT.")
    return matieres


def _nombre_fr(x: float, dec: int) -> str:
    """1.50 -> « 1,5 », 6.0 -> « 6 » : virgule française, zéros inutiles ôtés."""
    s = f'{x:.{dec}f}'.rstrip('0').rstrip('.')
    return (s or '0').replace('.', ',')


def injecter_coupe(corps: str, nom: str) -> str:
    """Remplace {{coupe.nb}} et {{coupe:table_matieres}} depuis l'appli.

    Le tableau est donné pour une fraise de 6 mm — le diamètre par défaut de
    l'appli — parce que fz et la passe y sont proportionnels au diamètre :
    une seule colonne d'exemple suffit à situer les ordres de grandeur.
    """
    if '{{coupe' not in corps:
        return corps
    lignes = []
    for m in matieres_coupe():
        broche = ('au maximum' if m['mode'] == 'rpm'
                  else f"Vc {_nombre_fr(m['vc'], 0)} m/min")
        fz6 = _nombre_fr(m['fz_par_mm'] * 6, 3)
        passe = f"{_nombre_fr(m['ap_lo'] * 6, 1)}–{_nombre_fr(m['ap_hi'] * 6, 1)}"
        lignes.append(f'<tr><td>{html.escape(m["label"])}</td>'
                      f'<td class="num">{broche}</td>'
                      f'<td class="num">{fz6}</td>'
                      f'<td class="num">{passe}</td>'
                      f'<td>{html.escape(m["note"])}</td></tr>')
    corps = corps.replace('{{coupe:table_matieres}}', '\n          '.join(lignes))
    corps = corps.replace('{{coupe.nb}}', str(len(matieres_coupe())))
    reste = re.findall(r'\{\{coupe[^}]*\}\}', corps)
    if reste:
        sys.exit(f"{nom} : marque coupe non résolue : {reste[0]}")
    return corps


def chapeau_en_ligne() -> str:
    """Le chapeau seul, prêt à être collé dans l'appli.

    Collé et non chargé en <img> : un fichier de moins à servir, et rien à
    charger hors-ligne. On retire l'en-tête XML et le commentaire, qui n'ont
    pas leur place au milieu d'un document HTML.
    """
    chemin = KIT / 'chapeau.svg'
    if not chemin.exists():
        sys.exit(f"generer : {chemin} manquant.")
    s = chemin.read_text(encoding='utf-8')
    return s[s.index('<svg'):].strip()


def version_appli_coupe() -> str:
    """La version de l'appli, LUE dans le `CACHE` de son service worker.

    Une seule source : la constante que l'on incrémente déjà à chaque
    retouche pour renouveler le cache. La pastille affichée dans l'appli et
    le version.json interrogé au réseau en sortent tous les deux, donc ils
    ne peuvent pas diverger — c'est tout l'intérêt, puisque leur comparaison
    est précisément ce qui dit au visiteur s'il est à jour.
    """
    sw = APPLI_COUPE / 'sw.js'
    m = re.search(r'^const CACHE = "coupe-(v\d+)"', sw.read_text(encoding='utf-8'),
                  re.M)
    if not m:
        sys.exit(f"generer : version introuvable dans {sw} — la ligne "
                 f"« const CACHE = \"coupe-vN\" » a dû changer de forme.")
    return m.group(1)


def copier_appli_coupe() -> None:
    """Recopie l'appli « vitesses de coupe » TELLE QUELLE dans public/coupe/.

    Pas d'empreinte de contenu dans les noms, et c'est voulu : l'appli
    embarque un service worker, et c'est LUI la politique de cache — la
    constante CACHE de sw.js, à incrémenter à chaque retouche de l'appli.
    Ses chemins (start_url du manifest, sw.js) doivent rester stables pour
    que les téléphones qui l'ont installée la retrouvent.
    """
    if not APPLI_COUPE.is_dir():
        sys.exit("generer : site/appli/coupe/ introuvable — l'appli fait "
                 "partie du site.")
    shutil.copytree(APPLI_COUPE, PUBLIC / 'coupe')

    # Le chapeau de la maison est POSÉ ICI, jamais recopié dans l'appli : il
    # sort de kit/chapeau.svg, donc il suit le kit. En ligne et non en <img>
    # pour ne dépendre d'aucun fichier annexe hors-ligne ; son liseré blanc
    # le détache seul du fond noir de l'appli.
    index = PUBLIC / 'coupe' / 'index.html'
    texte = index.read_text(encoding='utf-8')
    if '<!--CHAPEAU_VERDIER-->' not in texte:
        sys.exit("generer : marque <!--CHAPEAU_VERDIER--> absente de l'appli "
                 "coupe — elle partirait en ligne sans la marque de la maison.")
    texte = texte.replace('<!--CHAPEAU_VERDIER-->', chapeau_en_ligne(), 1)

    # La VERSION, lue dans le `CACHE` du service worker — une seule valeur,
    # jamais recopiée. Elle sert deux fois : affichée dans la pastille de
    # l'appli, et écrite dans version.json que l'appli interroge au réseau
    # pour savoir si elle est à jour.
    version = version_appli_coupe()
    if '{{VERSION}}' not in texte:
        sys.exit("generer : marque {{VERSION}} absente de l'appli coupe — "
                 "la pastille de version ne saurait pas quoi afficher.")
    texte = texte.replace('{{VERSION}}', version, 1)
    index.write_text(texte, encoding='utf-8')
    (PUBLIC / 'coupe' / 'version.json').write_text(
        '{"version": "%s"}\n' % version, encoding='utf-8')

    n = len(list((PUBLIC / 'coupe').iterdir()))
    print(f"  appli coupe → coupe/ ({n} fichiers, {version}, chapeau posé)")


def partage_appli_coupe() -> None:
    """Donne à l'appli /coupe/ sa carte Facebook et ses balises Open Graph.

    L'appli est copiée HORS du gabarit entete.html — c'est ce qui lui garde
    son identité d'appli plein écran. Mais du coup elle n'hérite d'AUCUNE
    balise og : partagée telle quelle sur Facebook, elle n'affichait ni image
    ni description, juste le domaine et le titre (vu le 24/08/2026 en
    partageant atelierduverdier.fr/coupe/). On lui fabrique donc ici la même
    carte de marque 1200x630 que les pages sans image, et on injecte ses
    balises dans la copie servie — automatiquement, à chaque génération, pour
    ne plus jamais avoir à y penser.

    JPEG et pas WebP : le robot de Facebook ne lit pas le WebP. Empreinte de
    contenu dans le nom : Facebook garde longtemps la dernière carte vue, une
    adresse figée lui ferait resservir l'ancienne après une correction.
    """
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.exit("generer : il faut Pillow pour la carte de partage de l'appli.")

    cible = PUBLIC / 'partage'
    cible.mkdir(parents=True, exist_ok=True)
    carte = carte_partage(None, COUPE_TITRE, COUPE_RESUME)   # carte de marque
    brut = cible / 'x-coupe.jpg'
    carte.save(brut, 'JPEG', quality=86, optimize=True, progressive=True)
    marque = hashlib.sha256(brut.read_bytes()).hexdigest()[:8]
    final = cible / f'coupe.{marque}.jpg'
    brut.replace(final)

    url = f"https://{DOMAINE}/coupe/"
    image = f"https://{DOMAINE}/partage/{final.name}"
    def att(s):
        return html.escape(s, quote=True)
    balises = '\n'.join([
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Atelier du Verdier">',
        '<meta property="og:locale" content="fr_FR">',
        f'<meta property="og:title" content="{att(COUPE_TITRE)}">',
        f'<meta property="og:description" content="{att(COUPE_DESCRIPTION)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{image}">',
        '<meta property="og:image:type" content="image/jpeg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{att(COUPE_TITRE)}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])

    index = PUBLIC / 'coupe' / 'index.html'
    texte = index.read_text(encoding='utf-8')
    ancre = '<link rel="manifest" href="./manifest.webmanifest">'
    if ancre not in texte:
        sys.exit("generer : ancre manifest introuvable dans l'appli coupe — "
                 "impossible d'injecter les balises de partage.")
    texte = texte.replace(ancre, ancre + '\n' + balises, 1)
    index.write_text(texte, encoding='utf-8')
    print(f"  partage appli coupe → {final.name} + balises og injectées")


def compteur_prefixe() -> str:
    """Le bout de script qui préfixe les chemins remontés au compteur.

    Posé AVANT count.js : le script lit `window.goatcounter` au chargement.
    `path` accepte une fonction, qui reçoit le chemin courant et rend celui
    à enregistrer.
    """
    if not PREFIXE_COMPTEUR:
        return ''
    return (
        '<script>\n'
        '  window.goatcounter = {\n'
        f"    path: function (p) {{ return '{PREFIXE_COMPTEUR}' + p }}\n"
        '  };\n'
        '</script>'
    )


def logo_en_ligne() -> str:
    """Le logo, prêt à être collé dans une page.

    Collé et non chargé en <img> : son mot-symbole est en `currentColor`,
    il suit donc le bouton de thème. En <img>, il ne suivrait que le
    réglage du système. On retire l'en-tête XML et le commentaire, qui
    n'ont pas leur place au milieu d'un document HTML.
    """
    chemin = KIT / 'logo-inline.svg'
    if not chemin.exists():
        sys.exit(f"generer : {chemin.name} manquant — lancer d'abord "
                 f"« python3 kit/faire_logo.py ».")
    s = chemin.read_text(encoding='utf-8')
    return s[s.index('<svg'):].strip()

ANNEE = '2026'

# Domaine de production, écrit dans public/CNAME à chaque génération pour
# survivre à la reconstruction de public/.
#
# ARMÉ le 12/08/2026, et pas avant : tant que printnc-build réclamait
# atelierduverdier.fr auprès de GitHub, un CNAME posé ici serait entré en
# conflit. L'ordre a été DNS (OVH) → libération par le journal → cette
# ligne. Voir PLAN.md, chantier 2.
DOMAINE = 'atelierduverdier.fr'

# Préfixe des chemins remontés à GoatCounter. Le compte est commun à tout le
# domaine et n'enregistre PAS le nom d'hôte (vérifié dans count.js) : sans
# préfixe, le « / » du portail et celui du journal PrintNC se confondraient.
# C'est le nouveau venu qui se préfixe — le journal garde son historique.
# Vide ('') = pas de préfixe, pour un site qui serait seul sur son compte.
PREFIXE_COMPTEUR = '/portail'

# --- Les pages -----------------------------------------------------------
# `sortie` est relatif à public/ ; la profondeur en déduit {{RACINE}}.

PAGES = [
    {
        'contenu': 'accueil.html',
        'sortie': 'index.html',
        'titre': "Atelier du Verdier — l'atelier et ses logiciels",
        'description': "Une fraiseuse PrintNC, une tête laser, un traceur de découpe, "
                       "et les logiciels écrits pour les faire tourner : LaserAtelier, "
                       "visualiseur G-code LinuxCNC, pupitre Graphtec, config PrintNC.",
        'sous_titre': '',
        'resume': "L'atelier d'un menuisier-bricoleur outillé : une PrintNC, un laser "
                  "diode, un traceur de découpe, et le logiciel qui va avec.",
    },
    {
        'contenu': 'laseratelier.html',
        'sortie': 'logiciels/laseratelier.html',
        'partage': chemins.LASER_SHOTS / 'resultat-colore.png',
        'titre': "LaserAtelier — graver ce qui n'est pas plat",
        'description': "Atelier FreeCAD de G-code laser : suivi de surfaces courbes, "
                       "gravure remplie, photo tramée, découpe multi-passes. Pourquoi "
                       "un point ne peut pas être une temporisation, et pourquoi tout "
                       "se vérifie sur le bois.",
        'sous_titre': 'LaserAtelier',
        'resume': "Atelier FreeCAD pour le marquage et la découpe laser sur CNC, "
                  "surfaces courbes comprises. Code public, LGPL-2.1-or-later.",
    },
    {
        'contenu': 'visualiseur-gcode.html',
        'sortie': 'logiciels/visualiseur-gcode.html',
        'partage': CONTENU / 'captures' / 'visualiseur-paquerette.png',
        'titre': "Visualiseur de parcours G-code LinuxCNC",
        'description': "Un aperçu de trajectoire pour LinuxCNC qui ne ment pas sur les "
                       "fichiers paramétrés : il appelle rs274, l'interprète de LinuxCNC "
                       "lui-même, au lieu d'écrire un parseur de plus.",
        'sous_titre': 'visualiseur G-code',
        'resume': "Visualiseur de parcours LinuxCNC en PySide6/OpenGL, appuyé sur rs274. "
                  "Code public, LGPL-2.1.",
    },
    {
        'contenu': 'pupitre-graphtec.html',
        'sortie': 'logiciels/pupitre-graphtec.html',
        'partage': CONTENU / 'captures' / 'pupitre-machine.png',
        'titre': "Pupitre Graphtec CE6000-60 — piloter un traceur sous Linux",
        'description': "Piloter le traceur de découpe Graphtec CE6000-60 depuis Linux, "
                       "sans driver : conversion SVG vers HP-GL, réglage de la machine, "
                       "et le protocole propriétaire TC relevé au flux USB.",
        'sous_titre': 'pupitre Graphtec',
        'resume': "Pilotage du traceur de découpe Graphtec CE6000-60 sous Linux, sans "
                  "driver constructeur. Code public, GPL-3.0.",
    },
    {
        'contenu': 'vitesses-coupe.html',
        'sortie': 'logiciels/vitesses-coupe.html',
        'partage': CONTENU / 'captures' / 'appli-coupe.png',
        'titre': "Vitesses de coupe — l'abaque dans la poche",
        'description': "Appli web de poche pour choisir broche et avance au pied de "
                       "la fraiseuse : neuf matières du sapin à l'acier doux, "
                       "bibliothèque d'outils locale, export FreeCAD. Hors-ligne "
                       "une fois ouverte, rien n'est envoyé.",
        'sous_titre': 'vitesses de coupe',
        'resume': "Calculateur d'avances et de vitesses pour le fraisage CNC : "
                  "neuf matières, hors-ligne, rien n'est envoyé.",
    },
    {
        'contenu': 'attache-gouttiere.html',
        'sortie': 'projets/attache-gouttiere.html',
        'partage': chemins.ATTACHE_RENDU / 'planche_collier.png',
        'titre': "Attache de descente Ø 80 — un collier qui ne serre pas",
        'description': "Collier de descente de gouttière Ø 80 imprimé en PETG, "
                       "monté sur un insert récupéré des attaches cassées. Ses "
                       "oreilles viennent en butée : l'alésage reste à Ø 81 et le "
                       "tube coulisse pour se dilater.",
        'sous_titre': 'attache de descente',
        'resume': "Collier de descente Ø 80 imprimé, non serrant, sur insert "
                  "récupéré. Modèle FreeCAD paramétrique.",
    },
    {
        'contenu': 'modeles-3d.html',
        'sortie': 'modeles-3d.html',
        'titre': "Les objets en 3D — Atelier du Verdier",
        # ENGENDRÉE, PAS ÉCRITE. Elle annonçait « … armoire de jardin, porte
        # de hammam » pour une page qui n'a jamais porté que quatre objets, et
        # c'est ce texte-là que Google affiche et que Facebook déplie. Elle se
        # déduit désormais des cartes de la page — voir `faits_modeles`.
        'description': "Les modèles FreeCAD de l'atelier, manipulables dans le "
                       "navigateur : {{modeles:noms}}. Les mêmes fichiers que "
                       "ceux qui servent à usiner et à débiter.",
        'sous_titre': 'modèles 3D',
        'resume': "Les modèles FreeCAD de l'atelier, à faire tourner dans le "
                  "navigateur.",
        # Le visualiseur n'est chargé QUE par cette page : c'est toute la
        # raison d'avoir rassemblé les modèles ici plutôt que de les
        # disperser sur les pages projets.
        'entete_sup': '<style>\n'
                      '.cartes-3d model-viewer{width:100%;height:260px;display:block;\n'
                      '  margin:-4px 0 14px;border-radius:10px;background:var(--bg-3);\n'
                      '  --poster-color:transparent}\n'
                      '.cartes-3d .carte{padding:14px 16px 18px}\n'
                      '</style>',
        # Chemin ECRIT EN DUR, sans {{RACINE}} : `remplir` substitue RACINE
        # AVANT d'insérer LOCAL_JS, un {{RACINE}} placé ici ressortirait tel
        # quel. Cette page est à la racine, le chemin relatif suffit.
        'js_local': '<script type="module" '
                    'src="modeles/model-viewer.min.js"></script>',
    },
    {
        'contenu': 'projets.html',
        'sortie': 'projets/index.html',
        'titre': "Projets d'atelier — Atelier du Verdier",
        'description': "Les projets de l'atelier : magasin ATC ER20, tonnelle à jasmin, "
                       "meuble à balais, dust shoe. Tous paramétriques, pilotés par un "
                       "tableur, plans régénérables.",
        'sous_titre': 'projets',
        'resume': "Les projets d'atelier, chacun piloté par un tableur : on change une "
                  "valeur, les plans suivent.",
    },
    {
        'contenu': 'tonnelle-jasmin.html',
        'sortie': 'projets/tonnelle-jasmin.html',
        'partage': CONTENU / 'captures' / 'vue3d-tonnelle.png',
        'titre': "Tonnelle à jasmin — modèle paramétrique",
        'description': "Tonnelle en bois à tenons et mortaises, entièrement pilotée par "
                       "un tableur de 99 cotes : on change une valeur, les plans "
                       "d'exécution suivent.",
        'sous_titre': 'tonnelle',
        'resume': "Tonnelle à jasmin paramétrique, assemblages à tenons et mortaises.",
    },
    {
        'contenu': 'meuble-balais.html',
        'sortie': 'projets/meuble-balais.html',
        'partage': CONTENU / 'captures' / 'vue3d-meuble.png',
        'titre': "Meuble à balais — armoire de jardin paramétrique",
        'description': "Armoire de jardin à toit monopente et porte latérale, pilotée "
                       "par un tableur de 120 paramètres, avec sa feuille de débit "
                       "engendrée.",
        'sous_titre': 'meuble à balais',
        'resume': "Armoire de jardin paramétrique, feuille de débit engendrée avec le "
                  "modèle.",
    },
    {
        # L'ancienne adresse de la tonnelle. Elle a été servie du 12 au
        # 23/08/2026 sous « glycine » — le projet s'appelait ainsi par
        # erreur de plante. Une page renommée sans rien laisser derrière
        # transforme en 404 tout lien déjà posé, et un 404 ne dit pas
        # « déménagé », il dit « cassé ».
        'contenu': 'redirection-tonnelle.html',
        'sortie': 'projets/tonnelle-glycine.html',
        'titre': "Tonnelle à jasmin — cette page a déménagé",
        'description': "Le projet « tonnelle à glycine » est en réalité une tonnelle "
                       "à jasmin : la page a changé d'adresse.",
        'sous_titre': 'tonnelle',
        'resume': "Cette adresse a déménagé vers projets/tonnelle-jasmin.html.",
        # La canonique passe par `canonique`, PAS par `entete_sup` : ecrite
        # a la main dans l'en-tete supplementaire, elle s'AJOUTAIT a celle
        # que le gabarit pose deja, et la page se retrouvait avec DEUX
        # canoniques contradictoires — l'une vers elle-meme, l'autre vers
        # jasmin. Des canoniques qui se contredisent sont ignorees : la
        # redirection ne protegeait donc rien, elle laissait cette page
        # concourir avec la vraie. Trouve le 27/08/2026 en verifiant les
        # pages projets.
        'canonique': 'https://atelierduverdier.fr/projets/tonnelle-jasmin.html',
        'entete_sup': '<meta http-equiv="refresh" content="0; url=tonnelle-jasmin.html">',
    },
    {
        'contenu': 'dust-shoe.html',
        'sortie': 'projets/dust-shoe.html',
        'partage': CONTENU / 'captures' / 'vue3d-dust-shoe-fraisage.png',
        'titre': "Dust shoe PrintNC — le laser et le tuyau se relaient",
        'description': "Aspiration pour broche Ø80 sur PrintNC : trois pièces "
                       "imprimées dont deux se retirent, et un adaptateur qui "
                       "prend la place du laser sur sa glissière. Jamais imprimé "
                       "ni essayé — le modèle et ses contrôles seulement.",
        'sous_titre': 'dust shoe',
        'resume': "Jupe d'aspiration paramétrique pour la broche G-PENNY Ø80 : "
                  "semelle à demeure, brosse amovible, adaptateur de tuyau Ø100.",
    },
    {
        'contenu': 'volets-battants.html',
        'sortie': 'projets/volets-battants.html',
        'titre': "Volets battants — deux battants qui ne font pas la meme largeur",
        'description': "Paire de volets battants en douglas, entierement "
                       "parametrique : chaque battant recalcule ses lames, ses "
                       "barres et son echarpe a partir de SA largeur. Rainure "
                       "filante, languettes fraisees, chevilles rondes. Planches "
                       "tracees a la plume sur un traceur de decoupe.",
        'sous_titre': 'volets battants',
        'resume': "Volets battants en douglas pour un tableau qui n'est pas "
                  "d'aplomb : 500 et 490 mm de large, tout pilote par un tableur.",
    },
    {
        'contenu': 'magasin-atc.html',
        'sortie': 'projets/magasin-atc.html',
        'titre': "Magasin ATC ER20 — la note de calcul de la bille",
        'description': "Comment trois billes acier Ø5 retiennent un écrou ER20 : "
                       "pourquoi la saillie vaut 1,20 mm, où la bille porte sur "
                       "l'écrou, et la contrainte la plus serrée du projet.",
        'sous_titre': 'magasin ATC',
        'resume': "Changeur d'outil automatique à billes pour broche ER20 sur PrintNC. "
                  "Notes de calcul et planches.",
    },
]

LIENS_PIED = [
    ('https://ko-fi.com/atelierduverdier', '☕ Ko-fi'),
    ('https://github.com/atelierduverdier', 'GitHub'),
    ('https://laser.atelierduverdier.fr', 'Atelier Laser'),
    ('https://printnc.atelierduverdier.fr', 'Journal PrintNC'),
    ('https://liens.atelierduverdier.fr', 'Mes liens'),
]


# Quelle entrée de menu s'allume, pour une page donnée.
#
# LA PASTILLE ÉTAIT DESSINÉE ET N'A JAMAIS SERVI. `kit/verdier.css` porte
# depuis le premier commit du dépôt, le 12/08/2026, une règle qui colore
# l'entrée courante en orange -- et rien n'a jamais posé l'attribut qu'elle
# attend. Relevé le 29/08 : `aria-current` n'apparaît nulle part dans les
# sources hors cette règle, et zéro fois dans les pages servies par les
# QUATRE sites. Soixante-quatorze commits et cinq pages devenues quatorze
# plus tard, la barre du haut -- collante, donc sous les yeux en permanence
# -- ne disait toujours pas où l'on est.
#
# Deux valeurs, et la nuance compte : `page` quand le lien mène exactement à
# la page affichée, `true` quand il mène à la RUBRIQUE qui la contient (une
# fiche projet allume « Projets » sans que « Projets » soit cette fiche).
# La règle CSS accepte les deux depuis qu'elle vise `a[aria-current]`.
RUBRIQUES = [
    ('modeles-3d.html', 'Modèles 3D'),
    ('projets/', 'Projets'),
    ('logiciels/', 'Logiciels'),
]

# Une redirection n'est pas une destination : elle sert un `meta refresh` et
# repart. Lui allumer une entrée ferait clignoter le menu au passage.
SANS_PASTILLE = {'projets/tonnelle-glycine.html'}


def entree_courante(sortie: str) -> tuple:
    """(libellé à allumer, valeur de l'attribut) pour la page en cours.

    L'accueil est le cas qui demande un arbitrage : TROIS entrées y mènent
    (« Accueil », et les deux ancres « Logiciels » et « L'atelier »). Sans
    choix explicite les trois s'allumeraient, ce qui est pire que rien --
    une barre où tout est allumé n'indique plus rien. C'est « Accueil » qui
    gagne : les deux autres ne désignent qu'une section de cette page.
    """
    if sortie in SANS_PASTILLE:
        return (None, None)
    if sortie == 'index.html':
        return ('Accueil', 'page')
    for prefixe, libelle in RUBRIQUES:
        if sortie == prefixe or sortie.startswith(prefixe):
            # Le sommaire d'une rubrique EST la page ; une fiche n'en est
            # qu'un membre.
            exact = sortie in (prefixe, prefixe + 'index.html')
            return (libelle, 'page' if exact else 'true')
    return (None, None)


def nav(prefixe: str, sortie: str = '') -> str:
    """Les liens de navigation, préfixés selon la profondeur de la page.

    `sortie` est le chemin de la page écrite : il sert à allumer son entrée.
    """
    entrees = [
        (prefixe + 'index.html', 'Accueil'),
        (prefixe + 'index.html#logiciels', 'Logiciels'),
        (prefixe + 'index.html#atelier', "L'atelier"),
        (prefixe + 'projets/', 'Projets'),
        (prefixe + 'modeles-3d.html', 'Modèles 3D'),
    ]
    allume, valeur = entree_courante(sortie)
    liens = []
    for u, t in entrees:
        marque = f' aria-current="{valeur}"' if t == allume else ''
        liens.append(f'<a href="{u}"{marque}>{t}</a>')
    return '\n      '.join(liens)


def liens_pied() -> str:
    return '\n      '.join(
        f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for u, t in LIENS_PIED
    )


def injecter_valeurs_atc(corps: str, nom: str) -> str:
    """Remplace les {{atc.cle}} et {{atc:table}} par les valeurs du MODÈLE.

    `{{atc.saillie}}`      -> 1,20   (2 décimales par défaut)
    `{{atc.chambre|0}}`    -> 35
    `{{atc:table_saillie}}`-> les lignes du tableau, engendrées

    Une clé inconnue arrête la génération : mieux vaut pas de page qu'une
    page où il manque un nombre, ou pire, où il en traîne un périmé.
    """
    if '{{atc' not in corps:
        return corps

    v = valeurs_atc.charger()
    manquantes = []

    def remplacer(m):
        cle, decimales = m.group(1), m.group(2)
        if cle not in v:
            manquantes.append(cle)
            return m.group(0)
        return valeurs_atc.nombre(v[cle], int(decimales) if decimales else 2)

    corps = corps.replace('{{atc:table_saillie}}', valeurs_atc.table_saillie())
    corps = re.sub(r'\{\{atc\.(\w+)(?:\|(\d+))?\}\}', remplacer, corps)

    if manquantes:
        sys.exit(f"{nom} : grandeur(s) absente(s) du modèle ATC : "
                 f"{', '.join(sorted(set(manquantes)))}")
    reste = re.findall(r'\{\{atc[.:](\w+)[^}]*\}\}', corps)
    if reste:
        sys.exit(f"{nom} : {{{{atc}}}} non résolu : {', '.join(sorted(set(reste)))}")
    return corps


def remplir(gabarit: str, valeurs: dict, nom: str) -> str:
    """Remplace les {{MARQUES}} et refuse de laisser passer un trou.

    Une marque oubliée s'afficherait telle quelle sur la page. Mieux vaut
    que la génération s'arrête que de publier « {{TITRE}} ».
    """
    for cle, valeur in valeurs.items():
        gabarit = gabarit.replace('{{' + cle + '}}', valeur)
    restantes = set(re.findall(r'\{\{(\w+)\}\}', gabarit))
    if restantes:
        sys.exit(f"{nom} : marque(s) non remplacée(s) : {', '.join(sorted(restantes))}")
    return gabarit


def _police(taille, gras=False):
    from PIL import ImageFont
    return ImageFont.truetype(POLICE % ('-Bold' if gras else ''), taille)


def _chapeau(hauteur):
    """Le chapeau de la maison, rasterisé depuis le SVG du kit.

    Rasterisé et non redessiné : c'est la même image que la favicon et que
    les icônes du greffon. Il est noir et orange — d'où le fond CLAIR de la
    carte, sur une ardoise il disparaîtrait.
    """
    from PIL import Image
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        sortie = f.name
    r = subprocess.run(['rsvg-convert', '-h', str(hauteur),
                        str(KIT / 'chapeau.svg'), '-o', sortie],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    im = Image.open(sortie).convert('RGBA')
    Path(sortie).unlink()      # ce fichier n'a rien à faire dans /tmp
    return im


def _ecourter(texte, n):
    """Coupe sur un espace, jamais en plein mot, et pose les points."""
    if len(texte) <= n:
        return texte
    coupe = texte[:n].rsplit(' ', 1)[0]
    return coupe.rstrip(' ,;:') + '…'


def _replier(texte, largeur, lignes_max):
    """Replie un texte en lignes de `largeur` caractères au plus.

    Ce qui dépasse est écourté sur la dernière ligne, pas tranché : la
    version d'avant rendait « une PrintNC, un laser diode, un t ».
    """
    if not texte:
        return []
    mots, lignes, courante = texte.split(), [], ''
    for m in mots:
        essai = (courante + ' ' + m).strip()
        if len(essai) <= largeur:
            courante = essai
            continue
        lignes.append(courante)
        courante = m
        if len(lignes) == lignes_max:
            break
    else:
        if courante:
            lignes.append(courante)
    if len(lignes) > lignes_max:
        lignes = lignes[:lignes_max]
    reste = len(' '.join(lignes)) < len(texte)
    if reste and lignes:
        lignes[-1] = _ecourter(lignes[-1] + ' …', largeur)
    return lignes


def carte_partage(source, titre, sous_titre):
    """Compose la vignette 1200 x 630 d'une page.

    Avec une image : elle est CONTENUE (jamais recadrée — une planche
    rognée ne veut plus rien dire), sur le fond clair de la maison, avec un
    bandeau de marque en bas. Sans image : une carte de marque, titre
    compris. Toutes se ressemblent, c'est le but : partagées côte à côte,
    on doit voir qu'elles viennent du même atelier.
    """
    from PIL import Image, ImageDraw
    carte = Image.new('RGB', (PARTAGE_L, PARTAGE_H), PARTAGE_FOND)
    d = ImageDraw.Draw(carte)
    bandeau = 108                      # hauteur réservée à la marque

    if source is not None and source.exists():
        im = Image.open(source).convert('RGB')
        zone = (PARTAGE_L - 80, PARTAGE_H - bandeau - 56)
        im.thumbnail(zone, Image.LANCZOS)
        carte.paste(im, ((PARTAGE_L - im.width) // 2,
                         28 + (zone[1] - im.height) // 2))
        d.line([(40, PARTAGE_H - bandeau + 6), (PARTAGE_L - 40,
                PARTAGE_H - bandeau + 6)], fill=PARTAGE_ORANGE, width=3)
        ch = _chapeau(56)
        x = 40
        if ch:
            carte.paste(ch, (x, PARTAGE_H - bandeau + 26), ch)
            x += ch.width + 18
        d.text((x, PARTAGE_H - bandeau + 26), "Atelier du Verdier",
               font=_police(32, True), fill=PARTAGE_ENCRE)
        d.text((x, PARTAGE_H - bandeau + 64), "atelierduverdier.fr",
               font=_police(24), fill=PARTAGE_ORANGE)
        return carte

    ch = _chapeau(150)
    if ch:
        carte.paste(ch, ((PARTAGE_L - ch.width) // 2, 78), ch)
    def centre(txt, y, police, coul):
        l = d.textlength(txt, font=police)
        d.text(((PARTAGE_L - l) / 2, y), txt, font=police, fill=coul)
    centre("Atelier du Verdier", 248, _police(58, True), PARTAGE_ENCRE)

    # Le titre de page commence souvent par le nom du site : le répéter
    # sous lui donnait « Atelier du Verdier » deux fois, l'un sous l'autre.
    morceaux = [m.strip() for m in titre.split('—')]
    if morceaux and morceaux[0] == "Atelier du Verdier":
        morceaux = morceaux[1:]
    coupe = (' — '.join(morceaux)).strip()
    y = 326
    if coupe:
        centre(_ecourter(coupe, 46), y, _police(36, True), PARTAGE_ENCRE)
        y += 56
    # Et la phrase se coupe sur un ESPACE, sur deux lignes au plus : la
    # troncature brute rendait « un laser diode, un t ».
    for ligne in _replier(sous_titre, 62, 2):
        centre(ligne, y, _police(26), PARTAGE_GRIS)
        y += 36
    d.line([(450, 470), (750, 470)], fill=PARTAGE_ORANGE, width=3)
    centre("atelierduverdier.fr", 502, _police(28), PARTAGE_ORANGE)
    return carte


def images_partage(pages) -> dict:
    """Une vignette par page, nommée par l'empreinte de son contenu.

    L'empreinte n'est pas un ornement : Facebook garde très longtemps la
    carte qu'il a vue la première fois, et une adresse inchangée lui ferait
    resservir l'ancienne image après une correction.
    """
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.exit("generer : il faut Pillow pour les cartes de partage.")
    cible = PUBLIC / 'partage'
    cible.mkdir(parents=True, exist_ok=True)
    out, poids = {}, 0
    for page in pages:
        src = page.get('partage')
        src = Path(src) if src else None
        if src is not None and not src.exists():
            print(f"  ! image de partage absente : {src} — carte de marque")
            src = None
        carte = carte_partage(src, page['titre'], page.get('resume', ''))
        brut = cible / 'x.jpg'
        carte.save(brut, 'JPEG', quality=86, optimize=True, progressive=True)
        marque = hashlib.sha256(brut.read_bytes()).hexdigest()[:8]
        slug = page['sortie'].replace('/', '-').replace('.html', '')
        final = cible / f'{slug}.{marque}.jpg'
        brut.replace(final)
        out[page['sortie']] = final.name
        poids += final.stat().st_size
    print(f"  {len(out)} carte(s) de partage 1200x630 — {poids // 1024} Ko en JPEG")
    return out


def copier_ressources() -> dict:
    for nom in FICHIERS_KIT:
        shutil.copy2(KIT / nom, PUBLIC / nom)

    return convertir_captures()


def copier_modeles() -> dict:
    """Publie les modèles 3D et le visualiseur dans public/modeles/.

    MÊME RÈGLE QUE LES CAPTURES : une empreinte du contenu dans le nom. Un
    modèle re-exporté depuis FreeCAD change de contenu sans changer de nom,
    et le navigateur continuerait de montrer l'ancien — le pire des bogues,
    parce qu'il est invisible depuis le serveur.

    Le visualiseur, lui, garde son nom : c'est une bibliothèque figée. Son
    adresse stable le fait remettre en cache -- mais dix minutes seulement :
    GitHub Pages sert `cache-control: max-age=600`, et son ETag dérive de
    l'INSTANT DU DÉPLOIEMENT, pas du contenu. Un visiteur qui revient à la
    semaine le retélécharge donc entièrement.

    Rend ({clé: nom de fichier empreint}, {clé: octets TRANSMIS}).

    LE POIDS EST CELUI QUI PART SUR LE FIL, pas celui du disque. La page
    annonçait « 800 Ko en tout » -- la somme des fichiers -- alors que le
    serveur les gzippe et n'en transmet que 228. Une page dont toute la
    défense est la légèreté s'accusait ainsi de 3,5 fois son poids réel. On
    mesure donc la compression ici, au niveau 6 (celui des serveurs) : relevé
    le 29/08/2026, l'écart avec ce que sert GitHub Pages est de 3 %.
    """
    if not MODELES_3D.is_dir():
        return {}, {}
    cible = PUBLIC / 'modeles'
    cible.mkdir(parents=True, exist_ok=True)

    empreintes, transmis, total = {}, {}, 0
    for glb in sorted(MODELES_3D.glob('*.glb')):
        octets = glb.read_bytes()
        empreinte = hashlib.sha256(octets).hexdigest()[:10]
        nom = f'{glb.stem}.{empreinte}.glb'
        (cible / nom).write_bytes(octets)
        empreintes[glb.stem] = nom
        transmis[glb.stem] = len(zlib.compress(octets, 6))
        total += len(octets)

    visualiseur = VENDU / 'model-viewer.min.js'
    if visualiseur.is_file():
        shutil.copy2(visualiseur, cible / visualiseur.name)
        total += visualiseur.stat().st_size

    print(f"  modèles 3D → modeles/ ({len(empreintes)} modèle(s), "
          f"{sum(transmis.values()) // 1024} Ko transmis, "
          f"{total // 1024} Ko sur disque avec le visualiseur)")
    return empreintes, transmis


def injecter_attache(corps: str, nom: str) -> str:
    """Remplace `{{attache.cle}}` par la valeur écrite par le modèle.

    `{{attache.alesage}}`      -> 81
    `{{attache.prise_filet}}`  -> 4,7
    `{{attache.hors_tout}}`    -> 71 × 120,5 × 22
    `{{attache.jeu_insert|2}}` -> 0,60
    """
    if '{{attache.' not in corps:
        return corps
    for brut in sorted(set(re.findall(r'\{\{attache\.([\w.|]+)\}\}', corps))):
        cle, _, dec = brut.partition('|')
        valeur = valeurs_attache.valeur(cle, int(dec) if dec else 1)
        corps = corps.replace('{{attache.' + brut + '}}', valeur)
    return corps


# L'ETAT D'UN PROJET S'ECRIT UNE FOIS, ET PAS UNE DE PLUS.
#
# « modèle prêt, rien d'imprimé » était saisi A LA MAIN dans deux fichiers
# sans lien : le badge du héros de la page du projet, et la pastille de sa
# carte sur le sommaire. Le 28/08/2026 Christophe a écrit « c'est imprimé et
# c'est bien » — et il fallait corriger les deux, sous peine de laisser les
# deux pages du site se contredire.
#
# C'est exactement la faute que ce dépôt combat partout ailleurs : les cotes
# viennent de `valeurs.json`, le nombre de projets se compte, la VERSION de
# LaserAtelier se lit dans son source. L'état du projet était le dernier
# rescapé du régime de la recopie.
#
# La couleur de la pastille est PORTEE PAR L'ETAT, pas choisie à l'usage :
# `public` (vert) est réservé à ce qui a rencontré le réel.
ETATS = {
    'attache': ('public', 'posé sur la descente'),
}


def injecter_etat(corps: str, nom: str) -> str:
    """Remplace `{{etat:cle}}` et `{{etat-mot:cle}}`.

    `{{etat:attache}}`     -> <span class="etat public">posé sur la descente</span>
    `{{etat-mot:attache}}` -> posé sur la descente

    Une clé inconnue ARRETE la génération : une carte de projet sans état
    n'est pas une carte dégradée, c'est une carte qui ment par omission.
    """
    for marque, cle in sorted(set(re.findall(r'\{\{(etat|etat-mot):([\w-]+)\}\}',
                                            corps))):
        if cle not in ETATS:
            sys.exit(f"generer : {nom} demande l'état « {cle} », absent "
                     f"d'ETATS dans generer.py.")
        classe, mot = ETATS[cle]
        remplacement = (mot if marque == 'etat-mot'
                        else f'<span class="etat {classe}">{mot}</span>')
        corps = corps.replace('{{' + marque + ':' + cle + '}}', remplacement)
    return corps


def injecter_compte(corps: str, nom: str) -> str:
    """Remplace `{{cartes}}` par le nombre de cartes de la page, en toutes lettres.

    Le titre du sommaire des projets disait « Cinq projets » pendant que la
    page en portait SIX — la carte de l'attache de descente venait d'arriver.
    C'est la faute des nombres recopiés à la main, déjà payée sur la VERSION
    de LaserAtelier restée 44 versions en retard : un compte écrit ailleurs
    que là où on compte finit toujours par mentir.

    On ne compte donc pas ici non plus : on compte les `class="carte"` de la
    page elle-même, au moment de l'écrire.
    """
    if '{{cartes}}' not in corps:
        return corps
    n = corps.count('class="carte"')
    lettres = {1: 'Un', 2: 'Deux', 3: 'Trois', 4: 'Quatre', 5: 'Cinq',
               6: 'Six', 7: 'Sept', 8: 'Huit', 9: 'Neuf', 10: 'Dix',
               11: 'Onze', 12: 'Douze'}
    if n not in lettres:
        sys.exit(f"generer : {nom} porte {n} carte(s) — au-delà de douze, "
                 f"écrire le titre autrement que par un nombre en lettres.")
    return corps.replace('{{cartes}}', lettres[n])


def injecter_modeles(corps: str, nom: str, empreintes: dict) -> str:
    """Remplace `{{modele:clé}}` par le nom de fichier empreint.

    Une clé inconnue ARRÊTE la génération : une page de modèles 3D dont un
    modèle manque n'est pas une page dégradée, c'est une page fausse — le
    visualiseur y afficherait un cadre vide sans rien dire.
    """
    if '{{modele:' not in corps:
        return corps
    for cle in sorted(set(re.findall(r'\{\{modele:([\w-]+)\}\}', corps))):
        if cle not in empreintes:
            sys.exit(f"generer : {nom} demande le modèle « {cle} », absent de "
                     f"contenu/modeles/. Le produire avec "
                     f"outils/exporter_glb.py, ou retirer le bloc.")
        corps = corps.replace('{{modele:' + cle + '}}', empreintes[cle])
    return corps



def faits_modeles(corps: str, transmis: dict, nom: str) -> dict:
    """Ce que la page de modèles 3D montre VRAIMENT : compte, poids, noms.

    ON COMPTE SUR LA PAGE, PAS À CÔTÉ. La description de partage annonçait
    « collier de gouttière, sabot d'aspiration, tonnelle, armoire de jardin,
    PORTE DE HAMMAM » pour une page qui n'a jamais porté que quatre objets.
    Cette phrase-là n'est pas un détail interne : c'est ce que Google affiche
    dans ses résultats et ce que Facebook déplie quand on partage le lien.
    Quelqu'un cliquait pour une porte de hammam et ne la trouvait pas.

    Les pastilles du héros mentaient de leur côté -- « 4 modèles », « 800 Ko
    en tout » -- pour la même raison : trois nombres recopiés à la main, dans
    un site qui compte ses projets, lit la VERSION du greffon dans son source
    et tire les cotes des tableurs FreeCAD. C'était le dernier rescapé du
    régime de la recopie.

    Tout se déduit donc du corps de la page : chaque carte qui porte un
    `<model-viewer>` donne un objet, son `src` donne le poids transmis, son
    `<h3>` donne le nom. Ajouter une carte suffit ; retirer un modèle aussi.
    """
    cartes = [bloc for bloc in corps.split('class="carte"')
              if '<model-viewer' in bloc]
    if not cartes:
        sys.exit(f"generer : {nom} demande {{{{modeles:…}}}} mais ne porte "
                 f"aucune carte avec un <model-viewer>.")

    noms, octets = [], 0
    for bloc in cartes:
        titre = re.search(r'<h3>([^<]+)</h3>', bloc)
        fichier = re.search(r'<model-viewer[^>]*\bsrc="[^"]*/([\w-]+)\.\w+\.glb"',
                            bloc)
        if not titre or not fichier:
            sys.exit(f"generer : {nom} porte une carte 3D sans titre ou sans "
                     f"modèle lisible — le compte serait faux.")
        noms.append(titre.group(1).strip())
        octets += transmis.get(fichier.group(1), 0)

    # Minuscule à l'initiale : ces noms s'enfilent dans une phrase.
    en_phrase = [n[0].lower() + n[1:] for n in noms]
    return {
        'compte': str(len(noms)),
        'poids': f'{round(octets / 1024)} Ko',
        'noms': ', '.join(en_phrase[:-1]) + ' et ' + en_phrase[-1]
                if len(en_phrase) > 1 else en_phrase[0],
    }


def injecter_faits_modeles(texte: str, faits: dict, nom: str) -> str:
    """Remplace `{{modeles:compte|poids|noms}}`. Clé inconnue = arrêt."""
    if '{{modeles:' not in texte:
        return texte
    for cle in sorted(set(re.findall(r'\{\{modeles:(\w+)\}\}', texte))):
        if cle not in faits:
            sys.exit(f"generer : {nom} demande {{{{modeles:{cle}}}}}, qui "
                     f"n'existe pas. Connues : {', '.join(sorted(faits))}.")
        texte = texte.replace('{{modeles:' + cle + '}}', faits[cle])
    return texte

def empreinter(corps: str, empreintes: dict) -> str:
    """Remplace `captures/x.webp` par `captures/x.<empreinte>.webp`.

    **Un nom de fichier qui ne change pas est un mensonge que le cache
    répète.** Le 12/08/2026, une planche corrigée a continué de s'afficher
    dans sa version d'avant : le serveur envoyait la bonne image, mais le
    navigateur gardait l'ancienne — rien dans l'adresse ne lui disait que le
    contenu avait bougé. Une empreinte du contenu dans le nom rend la faute
    impossible : contenu différent, adresse différente, cache contourné.

    C'est la même règle que partout ici — ne pas recopier une valeur —
    appliquée à un nom de fichier.
    """
    for ancien, neuf in empreintes.items():
        corps = corps.replace(f'captures/{ancien}', f'captures/{neuf}')
    return corps


def convertir_captures() -> dict:
    """Publie les captures en WebP. Les PNG de `contenu/` restent les maîtres.

    LE CHOIX DU MODE EST MESURÉ, PAS SUPPOSÉ. Sur une interface à aplats —
    le pupitre, le visualiseur — le WebP **sans perte** bat le lossy de
    moitié (77 Ko contre 153 à q92) : peu de couleurs, de grandes zones
    unies. Sur une capture qui contient un rendu 3D ou des dégradés, c'est
    l'inverse (350 Ko sans perte, 96 Ko à q92). On encode donc les deux et
    on garde le plus petit, image par image.

    q92 et non q80 : ces captures sont pleines de texte de 11 px, et c'est
    lui qui se salit en premier quand on descend en qualité.
    """
    # Declare AVANT la premiere sortie : `empreintes` est le contrat de
    # cette fonction, chaque chemin doit pouvoir le rendre.
    empreintes = {}
    captures = CONTENU / 'captures'
    if not captures.is_dir():
        return empreintes
    try:
        from PIL import Image
    except ImportError:
        sys.exit("generer : il faut Pillow pour publier les captures en WebP.")

    cible = PUBLIC / 'logiciels' / 'captures'
    cible.mkdir(parents=True, exist_ok=True)

    avant = apres = 0
    sans_perte = 0
    for src in sorted(captures.glob('*.png')):
        image = Image.open(src).convert('RGB')
        dest = cible / (src.stem + '.webp')

        image.save(dest, 'WEBP', lossless=True, method=6)
        taille_sp = dest.stat().st_size
        image.save(dest, 'WEBP', quality=92, method=6)
        taille_q = dest.stat().st_size
        if taille_sp <= taille_q:
            image.save(dest, 'WEBP', lossless=True, method=6)
            sans_perte += 1

        # L'empreinte porte sur le WEBP, pas sur le PNG : c'est le fichier
        # servi, et c'est lui que le navigateur garde. Huit caractères
        # suffisent — on nomme des images, on ne signe rien.
        marque = hashlib.sha256(dest.read_bytes()).hexdigest()[:8]
        final = cible / f'{src.stem}.{marque}.webp'
        dest.replace(final)
        empreintes[f'{src.stem}.webp'] = final.name

        avant += src.stat().st_size
        apres += final.stat().st_size

    # LES VIDÉOS NE SE CONVERTISSENT PAS, elles se recopient — mais avec
    # la même empreinte de contenu dans le nom. Un fichier qui change sous
    # un nom qui ne change pas est un mensonge que le cache répète, et
    # c'est encore plus vrai d'un mégaoctet de vidéo que d'une image.
    poids_video = 0
    for src in sorted(captures.glob('*.mp4')):
        marque = hashlib.sha256(src.read_bytes()).hexdigest()[:8]
        final = cible / f'{src.stem}.{marque}.mp4'
        shutil.copy2(src, final)
        empreintes[f'{src.stem}.mp4'] = final.name
        poids_video += final.stat().st_size
    if poids_video:
        print(f"  {len(list(captures.glob('*.mp4')))} vidéo(s) recopiée(s) — "
              f"{poids_video // 1024} Ko, nommées par empreinte")

    n = len(list(captures.glob('*.png')))
    if n:
        print(f"  {n} capture(s) en WebP — {avant // 1024} Ko → {apres // 1024} Ko "
              f"({100 - 100 * apres // avant} % de moins, {sans_perte} sans perte, "
              f"nommées par empreinte)")

    cible = PUBLIC / 'projets' / 'plans'
    cible.mkdir(parents=True, exist_ok=True)
    for dossier, noms in PLANS_REPRIS:
        if not dossier.is_dir():
            print(f"  ! planches introuvables ({dossier}) — page sans planches")
            continue
        for nom in noms:
            source = dossier / nom
            if source.exists():
                shutil.copy2(source, cible / nom)
            else:
                print(f"  ! planche absente : {source}")

    return empreintes

def main() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)

    entete = (KIT / 'entete.html').read_text(encoding='utf-8')
    pied = (KIT / 'pied.html').read_text(encoding='utf-8')
    logo = logo_en_ligne()

    empreintes = copier_ressources()
    modeles, poids_modeles = copier_modeles()
    copier_appli_coupe()
    partage_appli_coupe()
    cartes = images_partage(PAGES)

    if DOMAINE:
        (PUBLIC / 'CNAME').write_text(DOMAINE + '\n', encoding='utf-8')
        print(f"  CNAME → {DOMAINE}")

    for page in PAGES:
        sortie = PUBLIC / page['sortie']
        sortie.parent.mkdir(parents=True, exist_ok=True)

        # Profondeur -> préfixe. index.html est à la racine : préfixe vide.
        profondeur = len(Path(page['sortie']).parts) - 1
        prefixe = '../' * profondeur

        corps = (CONTENU / page['contenu']).read_text(encoding='utf-8')
        corps = injecter_valeurs_atc(corps, page['contenu'])
        corps = injecter_laser(corps, page['contenu'])
        corps = injecter_fcstd(corps, page['contenu'])
        corps = injecter_coupe(corps, page['contenu'])
        corps = injecter_modeles(corps, page['contenu'], modeles)
        corps = injecter_attache(corps, page['contenu'])
        corps = injecter_compte(corps, page['contenu'])
        corps = injecter_etat(corps, page['contenu'])
        # Les faits se comptent SUR LA PAGE, une fois les modèles injectés :
        # ils servent au corps ET à la description de partage, qui ne peuvent
        # donc plus se contredire.
        faits = (faits_modeles(corps, poids_modeles, page['contenu'])
                 if '{{modeles:' in corps + page['description'] else {})
        corps = injecter_faits_modeles(corps, faits, page['contenu'])
        corps = corps.replace('{{LOGO}}', logo)
        corps = corps.replace('{{RACINE}}', prefixe)
        corps = empreinter(corps, empreintes)

        html = (
            remplir(entete, {
                'LOGO': logo,
                'TITRE': page['titre'],
                'DESCRIPTION': injecter_faits_modeles(
                    page['description'], faits, page['contenu']),
                'RACINE': prefixe,
                'SOUS_TITRE': page['sous_titre'],
                'NAV': nav(prefixe, page['sortie']),
                'LOCAL_CSS': page.get('entete_sup', ''),
                # `canonique` : l'adresse que cette page DECLARE etre la
                # sienne, quand ce n'est pas la ou elle est servie. Le cas
                # est celui d'une page de redirection : elle doit designer
                # sa destination, sinon elle CONCOURT avec elle.
                'OG_URL': page.get('canonique') or
                          f"https://{DOMAINE}/{page['sortie']}".replace(
                              '/index.html', '/'),
                'OG_IMAGE': f"https://{DOMAINE}/partage/{cartes[page['sortie']]}",
                'OG_ALT': page['sous_titre'] or 'Atelier du Verdier',
            }, 'entete.html')
            + '\n' + corps + '\n'
            + remplir(pied, {
                'COMPTEUR_PREFIXE': compteur_prefixe(),
                'LOGO': logo,
                'RACINE': prefixe,
                'SOUS_TITRE': page['sous_titre'],
                'RESUME': page['resume'],
                'LIENS': liens_pied(),
                'ANNEE': ANNEE,
                'LOCAL_JS': page.get('js_local', ''),
            }, 'pied.html')
        )

        sortie.write_text(html, encoding='utf-8')
        print(f"  {page['sortie']:<32} {sortie.stat().st_size:>7} o")

    total = sum(f.stat().st_size for f in PUBLIC.rglob('*') if f.is_file())
    print(f"\n{len(PAGES)} page(s) — public/ pèse {total // 1024} Ko")
    print(f"à ouvrir : file://{PUBLIC / 'index.html'}")


if __name__ == '__main__':
    main()
