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

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chemins
import valeurs_atc
import valeurs_fcstd

RACINE = Path(__file__).resolve().parent.parent
KIT = RACINE / 'kit'
SITE = RACINE / 'site'
CONTENU = SITE / 'contenu'
PUBLIC = SITE / 'public'

# Planches TechDraw reprises telles quelles depuis le projet ATC. Elles ne
# sont PAS régénérées ici : le modèle FreeCAD en est la source.
PLANS_ATC = chemins.ATC_PLANS
PLANS_REPRIS = [
    '07-ensemble-monte.svg',
    '01-siege-billes.svg',
    '08-gabarit-essai.svg',
]

FICHIERS_KIT = ['verdier.css', 'verdier.js', 'chapeau.svg', 'logo.svg']


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
        'titre': "Pupitre Graphtec CE6000-60 — piloter un traceur sous Linux",
        'description': "Piloter le traceur de découpe Graphtec CE6000-60 depuis Linux, "
                       "sans driver : conversion SVG vers HP-GL, réglage de la machine, "
                       "et le protocole propriétaire TC relevé au flux USB.",
        'sous_titre': 'pupitre Graphtec',
        'resume': "Pilotage du traceur de découpe Graphtec CE6000-60 sous Linux, sans "
                  "driver constructeur. Code public, GPL-3.0.",
    },
    {
        'contenu': 'projets.html',
        'sortie': 'projets/index.html',
        'titre': "Projets d'atelier — Atelier du Verdier",
        'description': "Les projets de l'atelier : magasin ATC ER20, tonnelle à glycine, "
                       "meuble à balais, dust shoe. Tous paramétriques, pilotés par un "
                       "tableur, plans régénérables.",
        'sous_titre': 'projets',
        'resume': "Les projets d'atelier, chacun piloté par un tableur : on change une "
                  "valeur, les plans suivent.",
    },
    {
        'contenu': 'tonnelle-glycine.html',
        'sortie': 'projets/tonnelle-glycine.html',
        'titre': "Tonnelle à glycine — modèle paramétrique",
        'description': "Tonnelle en bois à tenons et mortaises, entièrement pilotée par "
                       "un tableur de 99 cotes : on change une valeur, les plans "
                       "d'exécution suivent.",
        'sous_titre': 'tonnelle',
        'resume': "Tonnelle à glycine paramétrique, assemblages à tenons et mortaises.",
    },
    {
        'contenu': 'meuble-balais.html',
        'sortie': 'projets/meuble-balais.html',
        'titre': "Meuble à balais — armoire de jardin paramétrique",
        'description': "Armoire de jardin à toit monopente et porte latérale, pilotée "
                       "par un tableur de 120 paramètres, avec sa feuille de débit "
                       "engendrée.",
        'sous_titre': 'meuble à balais',
        'resume': "Armoire de jardin paramétrique, feuille de débit engendrée avec le "
                  "modèle.",
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
    ('https://github.com/atelierduverdier', 'GitHub'),
    ('https://laser.atelierduverdier.fr', 'Atelier Laser'),
    ('https://printnc.atelierduverdier.fr', 'Journal PrintNC'),
    ('https://liens.atelierduverdier.fr', 'Mes liens'),
]


def nav(prefixe: str) -> str:
    """Les liens de navigation, préfixés selon la profondeur de la page."""
    entrees = [
        (prefixe + 'index.html', 'Accueil'),
        (prefixe + 'index.html#logiciels', 'Logiciels'),
        (prefixe + 'index.html#atelier', "L'atelier"),
        (prefixe + 'projets/', 'Projets'),
    ]
    return '\n      '.join(f'<a href="{u}">{t}</a>' for u, t in entrees)


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


def copier_ressources() -> None:
    for nom in FICHIERS_KIT:
        shutil.copy2(KIT / nom, PUBLIC / nom)

    convertir_captures()


def convertir_captures() -> None:
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
    captures = CONTENU / 'captures'
    if not captures.is_dir():
        return
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

        avant += src.stat().st_size
        apres += dest.stat().st_size

    n = len(list(captures.glob('*.png')))
    if n:
        print(f"  {n} capture(s) en WebP — {avant // 1024} Ko → {apres // 1024} Ko "
              f"({100 - 100 * apres // avant} % de moins, {sans_perte} sans perte)")

    if not PLANS_ATC.is_dir():
        print(f"  ! planches ATC introuvables ({PLANS_ATC}) — pages sans planches")
        return

    cible = PUBLIC / 'projets' / 'plans'
    cible.mkdir(parents=True, exist_ok=True)
    for nom in PLANS_REPRIS:
        source = PLANS_ATC / nom
        if source.exists():
            shutil.copy2(source, cible / nom)
        else:
            print(f"  ! planche absente : {nom}")


def main() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)

    entete = (KIT / 'entete.html').read_text(encoding='utf-8')
    pied = (KIT / 'pied.html').read_text(encoding='utf-8')
    logo = logo_en_ligne()

    copier_ressources()

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
        corps = corps.replace('{{LOGO}}', logo)
        corps = corps.replace('{{RACINE}}', prefixe)

        html = (
            remplir(entete, {
                'LOGO': logo,
                'TITRE': page['titre'],
                'DESCRIPTION': page['description'],
                'RACINE': prefixe,
                'SOUS_TITRE': page['sous_titre'],
                'NAV': nav(prefixe),
                'LOCAL_CSS': '',
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
                'LOCAL_JS': '',
            }, 'pied.html')
        )

        sortie.write_text(html, encoding='utf-8')
        print(f"  {page['sortie']:<32} {sortie.stat().st_size:>7} o")

    total = sum(f.stat().st_size for f in PUBLIC.rglob('*') if f.is_file())
    print(f"\n{len(PAGES)} page(s) — public/ pèse {total // 1024} Ko")
    print(f"à ouvrir : file://{PUBLIC / 'index.html'}")


if __name__ == '__main__':
    main()
