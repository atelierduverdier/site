#!/usr/bin/env python3
# =========================================================================
# diffuser_kit.py — recopie la charte commune dans les sites satellites
# =========================================================================
# LE POINT DU CHANTIER 3. La charte vit ici, dans kit/, et nulle part
# ailleurs. Ce script la recopie ; personne ne l'édite chez le satellite.
#
# Ce qui a motivé la règle : au moment du cadrage, DEUX sites existaient et
# les DEUX avaient déjà des chartes différentes. Une valeur recopiée à la
# main dans cinq fichiers finit toujours par diverger — c'est le même piège
# que la ligne VERSION restée 44 versions en retard.
#
# CE QUE CE SCRIPT FAIT : recopier les fichiers du kit, avec un bandeau qui
# dit d'où ils viennent, et REFUSER d'écraser une copie retouchée sur place.
#
# CE QU'IL NE FAIT PAS : toucher au HTML des satellites. Brancher une page
# sur la charte (remplacer un <style> en ligne par un <link>) est une
# opération de contenu, faite une fois, à la main, avec les yeux dessus.
# Ensuite seulement les fichiers restent synchronisés tout seuls. Un script
# qui réécrirait du HTML à l'aveugle serait exactement le genre d'automate
# qu'on regrette.
#
# LA DÉTECTION DE DIVERGENCE. Après chaque envoi, l'empreinte de chaque
# fichier posé est notée dans `.kit-empreintes.json`, chez le satellite. Au
# passage suivant, un fichier dont l'empreinte ne correspond plus a été
# édité sur place : le script s'arrête et le dit, plutôt que d'effacer en
# silence un travail que quelqu'un a cru bon de faire.
#
# UTILISATION :
#   python3 outils/diffuser_kit.py            # envoie
#   python3 outils/diffuser_kit.py --blanc    # dit ce qu'il ferait
#   python3 outils/diffuser_kit.py --forcer   # écrase même si retouché
# =========================================================================

import hashlib
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
KIT = RACINE / 'kit'
EMPREINTES = '.kit-empreintes.json'

# Les fichiers de la charte, et le nom sous lequel ils sont POSÉS chez le
# satellite. La marque fait partie de la charte autant que les couleurs.
#
# LES NOMS SONT PRÉFIXÉS, et ce n'est pas cosmétique : le site laser avait
# déjà son propre `assets/logo.svg` — 40 Ko, utilisé dans son héros — qu'une
# première version de ce script a écrasé par collision de nom. Restauré
# depuis git. Tout ce que pose le kit s'appelle désormais `verdier-*`.
FICHIERS = {
    'verdier.css': 'verdier.css',
    'verdier.js': 'verdier.js',
    'chapeau.svg': 'verdier-chapeau.svg',
    'logo.svg': 'verdier-logo.svg',
}

# TOUS LES SATELLITES NE PRENNENT PAS LA MÊME CHOSE.
#
# Un site qui part de rien prend la charte entière. Un site qui a DÉJÀ sa
# mise en page ne prend que les jetons : mesuré le 12/08/2026, le kit
# complet posé sous le journal PrintNC lui ajoutait 258 px, parce que
# `.hero h1` du kit est plus spécifique que le `.hero-titre` du journal.
# Dix-sept sélecteurs se croisent, et la spécificité en crée d'autres qui
# ne se voient pas au nom : on ne pose donc que ce qui est demandé.
JETONS_SEULS = {
    'verdier-jetons.css': 'verdier-jetons.css',
    'verdier.js': 'verdier.js',
    'chapeau.svg': 'verdier-chapeau.svg',
    'logo.svg': 'verdier-logo.svg',
}

# Les jetons NE PORTENT PAS la barre du haut — et c'est elle qui fait le
# chemin du retour vers le portail. Relevé le 18/08/2026 : le journal
# citait `atelierduverdier.fr` cinq fois, et les CINQ étaient
# `laser.atelierduverdier.fr`. Aucun lien vers la racine du domaine : un
# visiteur venu d'un reel Instagram n'avait pas de porte de sortie.
#
# `verdier-entete.css` (extrait par kit/extraire_entete.py) ajoute la
# section 3 de la charte, et rien d'autre : la barre, la marque, les liens,
# le bouton de thème. La page de liens n'en a pas besoin — c'est une carte
# centrée, sans barre, et elle pointe déjà vers les quatre adresses.
JETONS_ET_ENTETE = {**JETONS_SEULS,
                    'verdier-entete.css': 'verdier-entete.css'}

# nom lisible -> dossier où poser la charte, chez le satellite.
SATELLITES = {
    'site laser': ((Path.home() / '.local' / 'share' / 'FreeCAD' / 'v1-1'
                    / 'Mod' / 'LaserAtelier' / 'docs' / 'assets'), FICHIERS),
    'journal PrintNC': ((Path.home() / 'Projets' / 'site' / 'Site_PrintNC'
                         / 'kit_site' / 'kit'), JETONS_ET_ENTETE),
    # La page de liens garde sa mise en page — une carte centrée, rien de
    # commun avec un site à barre du haut et à sections — donc les jetons
    # seuls, comme le journal. Elle prend quand même `verdier.js` : la
    # bascule de thème y range son choix dans un cookie de domaine, et
    # c'est ce qui fait qu'un visiteur passant d'ici au site laser garde
    # son réglage. Le dépôt est servi tel quel par GitHub Pages : ce qui
    # est posé ici part en ligne au prochain push.
    'page de liens': ((Path.home() / 'Projets' / 'site' / 'Site_Liens'),
                      JETONS_SEULS),
}

BANDEAU = {
    '.css': "/* {t}\n   {s} */\n",
    '.js':  "/* {t}\n   {s} */\n",
    '.svg': "<!-- {t}\n     {s} -->\n",
}
TITRE = "ENGENDRÉ — ne pas éditer ici."
SOURCE = ("Ce fichier est une copie de kit/{nom} du dépôt atelierduverdier/site. "
          "Toute retouche faite ici sera écrasée : corriger la source, puis "
          "relancer outils/diffuser_kit.py.")


def avec_bandeau(chemin: Path) -> bytes:
    """Le contenu du fichier, précédé du bandeau qui dit d'où il vient.

    Pour un SVG, le bandeau se glisse APRÈS la déclaration XML : un
    commentaire avant `<?xml …?>` rend le document invalide, et QtSvg — qui
    lit ces mêmes fichiers côté LaserAtelier — ne rend alors rien, sans le
    dire.
    """
    texte = chemin.read_text(encoding='utf-8')
    modele = BANDEAU.get(chemin.suffix)
    if not modele:
        return texte.encode('utf-8')
    entete = modele.format(t=TITRE, s=SOURCE.format(nom=chemin.name))

    if chemin.suffix == '.svg' and texte.lstrip().startswith('<?xml'):
        i = texte.index('?>') + 2
        return (texte[:i] + '\n' + entete + texte[i:].lstrip('\n')).encode('utf-8')
    return (entete + texte).encode('utf-8')


def empreinte(donnees: bytes) -> str:
    return hashlib.md5(donnees).hexdigest()


def diffuser(nom: str, dossier: Path, fichiers: dict, blanc: bool,
             forcer: bool) -> int:
    if not dossier.parent.exists():
        print(f"  {nom} : dossier parent absent ({dossier.parent}) — ignoré")
        return 0

    journal = dossier / EMPREINTES
    connues = {}
    if journal.exists():
        connues = json.loads(journal.read_text(encoding='utf-8'))

    retouches, aposer, etrangers = [], [], []
    for f, pose in fichiers.items():
        source = KIT / f
        if not source.exists():
            sys.exit(f"diffuser_kit : {source} manquant.")
        neuf = avec_bandeau(source)
        cible = dossier / pose

        # Un fichier qui existe SANS qu'on l'ait jamais posé n'est pas à
        # nous : on ne l'écrase pas, même au premier passage.
        if cible.exists() and pose not in connues:
            etrangers.append(pose)
            continue

        # Retouché sur place = présent, connu, et différent À LA FOIS de ce
        # qu'on avait posé et de ce qu'on s'apprête à poser.
        if cible.exists() and pose in connues:
            actuel = empreinte(cible.read_bytes())
            if actuel != connues[pose] and actuel != empreinte(neuf):
                retouches.append(pose)
                # On NE saute PAS : --forcer doit pouvoir l'écraser. Une
                # première version faisait `continue` ici, et --forcer
                # annonçait « déjà à jour » sans rien écraser — le fichier
                # n'entrait jamais dans la liste à poser.
        if not cible.exists() or empreinte(cible.read_bytes()) != empreinte(neuf):
            aposer.append((pose, cible, neuf))

    if etrangers:
        print(f"  {nom} : ARRÊT — ces fichiers existent déjà et ne viennent "
              f"pas du kit : {', '.join(etrangers)}")
        print(f"           les renommer chez le satellite, ou changer le nom "
              f"posé dans FICHIERS.")
        return -1

    if retouches and not forcer:
        print(f"  {nom} : ARRÊT — retouché sur place : {', '.join(retouches)}")
        print(f"           corriger dans kit/, ou relancer avec --forcer")
        return -1

    if not aposer:
        print(f"  {nom} : déjà à jour")
        return 0

    for f, cible, neuf in aposer:
        if blanc:
            print(f"  {nom} : poserait {f}")
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(neuf)
        connues[f] = empreinte(neuf)
        print(f"  {nom} : {f} ({len(neuf) // 1024} Ko)")

    if not blanc:
        journal.write_text(json.dumps(connues, indent=2, sort_keys=True) + '\n',
                           encoding='utf-8')
    return len(aposer)


def main() -> None:
    blanc = '--blanc' in sys.argv
    forcer = '--forcer' in sys.argv
    if blanc:
        print("(--blanc : rien n'est écrit)")

    total = 0
    for nom, (dossier, fichiers) in SATELLITES.items():
        r = diffuser(nom, dossier, fichiers, blanc, forcer)
        if r < 0:
            sys.exit(1)
        total += r
    print(f"\n{total} fichier(s) {'à poser' if blanc else 'posé(s)'}")


if __name__ == '__main__':
    main()
