#!/usr/bin/env python3
# =========================================================================
# exporter_glb.py — un modèle 3D manipulable de chaque projet, pour le site
# =========================================================================
# Frère de rendre_3d.py : celui-là fait une IMAGE, celui-ci fait un objet
# qu'on peut tourner dans le navigateur. Même règle : rien n'est modelé ici,
# le modèle FreeCAD reste la seule source, et on travaille sur une COPIE.
#
# DEUX ÉTAPES, parce qu'aucun outil ne fait les deux :
#   1. FreeCAD maille chaque solide visible et note sa couleur d'affichage
#      — celle que Christophe a posée dans le document, pas une inventée.
#   2. Blender assemble ces STL, pose un matériau par pièce, exporte un
#      .glb unique.
#
# CINQ PIÈGES PAYÉS, dont trois sont déjà ceux de rendre_3d.py :
#
#  1. `ActiveView` n'est PAS la vue 3D — mais ici on n'en a pas besoin.
#  2. Il faut `FreeCADGui.showMainWindow()` : sans elle, pas de ViewObject,
#     donc pas de couleurs.
#  3. On travaille sur une COPIE.
#  4. L'export glTF de FreeCAD ne sert à rien : `Import.export` produit bien
#     un `.glb`, mais VIDE — 320 octets, buffer binaire à zéro (28/08/2026).
#  5. Blender prend la Base Color en LINÉAIRE. Donner les valeurs sRGB de la
#     charte telles quelles faisait sortir l'orange #ff8a00 en #ffc100 —
#     mesuré dans le navigateur en relisant les baseColorFactor du GLB.
#
# UTILISATION :
#   xvfb-run -a freecad --console site/outils/exporter_glb.py
# Le verdict se lit dans /tmp/exporter_glb.txt : la console de FreeCAD avale
# la sortie et ne remonte pas le code.
# =========================================================================

import json
import os
import shutil
import subprocess
import tempfile
import traceback
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
# Les GLB sont du CONTENU, au même titre que les captures : ils sont
# engendrés depuis les modèles FreeCAD mais commités, pour que le site se
# construise sans que FreeCAD ni Blender soient installés.
SORTIE = RACINE / 'site' / 'contenu' / 'modeles'
JOURNAL = Path(tempfile.gettempdir()) / 'exporter_glb.txt'

# Finesse du maillage. 0,25 mm suffit largement pour un objet qu'on regarde
# dans un navigateur, et divise le poids par rapport aux 0,04 des STL
# d'impression.
FLECHE = 0.25
ANGLE = 0.35
TRIANGLES_MAX = 40000            # au-delà, on le dit : la page serait lourde

# (clé, modèle FreeCAD, ce que la page en dit, page du site, pièces choisies,
#  pièces écartées, réglages de la feuille)
#
# « écartées » et pas « choisies » pour cacher une pièce, et la nuance est
# mesurée : nommer les quatre groupes du cabanon dans « choisies » les ferait
# tous retomber sur le gris par défaut, puisqu'un groupe ne porte pas de
# ShapeColor — c'est le défaut « cabanon TOUT BLANC » déjà payé ici. On
# laisse donc la descente normale faire son travail, et on retire un nom à
# l'arrivée.
#
# La cinquième entrée ne sert qu'aux documents dont l'état d'affichage
# enregistré n'est pas un bon guide. Le sabot est dans ce cas : son Quai, son
# Adaptateur et sa Brosse y dorment INVISIBLES, et c'est le Quai — la moitié
# du produit — qui manquait au premier export.
#
# Un modèle dont le document s'ouvre avec des dizaines d'objets visibles qui
# ne composent rien ne donne pas un GLB montrable : le magasin ATC est dans
# ce cas (216 objets visibles sur 516), il est ÉCARTÉ comme il l'est déjà
# dans rendre_3d.py. Ce n'est pas une régression, c'est le même constat.
MODELES = [
    ('attache-gouttiere',
     Path.home() / 'Projets/realisations/attache-gouttiere/AttacheGouttiere80.FCStd',
     "Collier de descente Ø 80, deux pièces imprimées et un insert récupéré.",
     # NOMMÉES A LA MAIN, parce que le document est enregistré TOUT
     # INVISIBLE depuis sa régénération du 29/08/2026 — un `.FCStd` écrit
     # sans interface fait naître ses ViewProviders à `Visibility=False`.
     # Sans cette liste : « aucun solide visible à exporter », et le GLB
     # publié serait resté celui d'AVANT l'inversion vis/écrou. Ce sont
     # exactement les cinq pièces que portait le GLB précédent.
     'projets/attache-gouttiere.html',
     ['Corps', 'Bride', 'Axe', 'Insert', 'PatteAVis'], None, None),
    # L'ASSEMBLAGE PARQUÉ, ET PAS LES PIÈCES EN VRAC. `sabot_v2.FCStd` est le
    # modèle de travail : ses pièces y sont posées à l'origine, côte à côte,
    # sans rapport entre elles — on voyait quatre objets flotter, et le Quai y
    # est même enregistré INVISIBLE. Christophe, 29/08/2026 : « je pense que tu
    # t'es trompé de fichier ». `AssemblageQuaiV2` les MONTE : la brosse dans
    # son quai, la machine remontée de 40 avec sa semelle et son adaptateur.
    # C'est le geste du parcage, pas un inventaire.
    ('dust-shoe',
     Path.home() / 'Projets/machine/dust-shoe/fcstd/AssemblageQuaiV2.FCStd',
     "Le sabot d'aspiration parqué : la brosse reste dans son quai, la "
     "machine repart avec sa semelle.",
     'projets/dust-shoe.html', None, None, None),
    ('tonnelle-jasmin',
     Path.home() / 'Projets/realisations/tonnelle-jasmin/Tonnelle.FCStd',
     "La tonnelle montée : poteaux, sablières, chevrons et plots.",
     'projets/tonnelle-jasmin.html', None, None, None),
    # LA PORTE S'OUVRE, ELLE NE DISPARAÎT PAS. Première réponse à « il serait
    # bien de voir l'intérieur » : l'écarter de l'export. Elle montrait le
    # dedans et mentait sur le meuble — Christophe l'a vu du premier coup
    # d'œil. Le MODÈLE porte désormais l'angle (`AnglePorte`, 0 par défaut,
    # pour que les planches et le débit ne bougent pas d'un trait) ; le site
    # se contente de CHOISIR une valeur sur sa copie. On ne place rien à la
    # main : on renseigne un paramètre que le modèle expose.
    ('meuble-balais',
     Path.home() / 'Projets/realisations/meuble-balais/MeubleABalais.FCStd',
     "L'armoire de jardin, porte ôtée : la cloison en travers et les "
     "étagères du fond.",
     'projets/meuble-balais.html', None, None, {'AnglePorte': 120}),
]

_lignes = []


def dire(texte):
    _lignes.append(texte)
    print(texte, flush=True)
    JOURNAL.write_text("\n".join(_lignes) + "\n", encoding='utf-8')


def _cible(o):
    """L'objet qui porte vraiment la couleur, derrière un lien.

    UN `App::Link` N'A PAS DE `ShapeColor` — piège déjà écrit dans le dépôt du
    magasin ATC, et retrouvé ici le 29/08/2026 : l'assemblage du sabot n'est
    fait QUE de liens, donc pas un seul « porteur de couleur », donc « aucun
    solide visible à exporter » sur un document où tout est visible. On colore
    le lien par ce qu'il vise.
    """
    return getattr(o, 'LinkedObject', None) or o


def _porte_une_couleur(o):
    """Un objet qui a une ShapeColor est une PIÈCE ; un groupe n'en a pas.

    C'est le discriminant, et il est net : mesuré le 28/08/2026, les cinq
    groupes du meuble à balais (Ossature, Bardage, Amenagement, Toiture,
    Porte) n'ont ni ShapeColor ni Transparency, là où chacune de leurs pièces
    en a une. Sans ce test on exportait les groupes, tous retombaient sur le
    gris par défaut, et le cabanon sortait TOUT BLANC."""
    vo = getattr(_cible(o), 'ViewObject', None)
    return vo is not None and hasattr(vo, 'ShapeColor')


def _enfants_solides(o):
    return [c for c in o.OutList
            if getattr(c, 'Shape', None) is not None and c.Shape.Solids]


def solides_a_exporter(doc, choisis=None, exclus=None):
    """Ce qu'on met dans le GLB, avec la couleur du document.

    TROIS RÈGLES, chacune payée par un défaut visible :

    1. On saute ce qui est TRANSPARENT. Une pièce translucide est un repère
       de construction, pas l'objet : le tronçon de tube et le fragment de
       mur du collier, le fantôme du laser du sabot. Dans un visualiseur ils
       ne font que voiler la pièce.
    2. Un GROUPE n'a pas de couleur. Soit on descend dans ses pièces, soit
       on garde sa forme et on lui prend la couleur de la première — le test
       est le VOLUME : si la somme des enfants vaut celle du groupe, c'est un
       assemblage et on descend ; sinon c'est une répétition (Draft Array),
       dont les enfants ne valent qu'un exemplaire, et on garde le groupe.
    3. `choisis` permet de nommer les pièces à la main, `exclus` d'en retirer
       après coup. Les deux ne se valent pas : `choisis` court-circuite la
       descente dans les groupes, donc une pièce nommée qui est un GROUPE sort
       au gris par défaut. Pour cacher la porte du cabanon on passe donc par
       `exclus`, qui laisse la descente colorer chaque planche avant de
       retirer le lot nommé.
    """
    exclus = set(exclus or ())
    def couleur_de(o):
        vo = getattr(_cible(o), 'ViewObject', None)
        return tuple(getattr(vo, 'ShapeColor', (0.72, 0.72, 0.74))[:3])

    def transparent(o):
        vo = getattr(_cible(o), 'ViewObject', None)
        return bool(getattr(vo, 'Transparency', 0))

    if choisis:
        retenus = []
        for nom in choisis:
            o = doc.getObject(nom) or next(
                (x for x in doc.Objects if x.Label == nom), None)
            if o is None:
                print(f"      (pièce « {nom} » introuvable)")
                continue
            retenus.append((o, couleur_de(o)))
        return retenus

    tetes = [o for o in doc.Objects
             if getattr(o, 'Shape', None) is not None and o.Shape.Solids
             and not [p for p in o.InList if hasattr(p, 'Shape')]
             and getattr(getattr(o, 'ViewObject', None), 'Visibility', False)]

    retenus = []
    for o in tetes:
        if o.Name in exclus or o.Label in exclus:
            continue
        if _porte_une_couleur(o):
            if not transparent(o):
                retenus.append((o, couleur_de(o)))
            continue
        # un groupe : assemblage ou répétition ?
        enfants = [c for c in _enfants_solides(o) if _porte_une_couleur(c)]
        if not enfants:
            continue
        somme = sum(c.Shape.Volume for c in enfants)
        assemblage = abs(somme - o.Shape.Volume) <= 0.02 * max(o.Shape.Volume, 1.0)
        if assemblage:
            for c in enfants:
                if c.Name in exclus or c.Label in exclus:
                    continue
                if not transparent(c):
                    retenus.append((c, couleur_de(c)))
        else:
            retenus.append((o, couleur_de(enfants[0])))
    # UN NOM ÉCARTÉ QUI NE DÉSIGNE RIEN DOIT SE DIRE. Sans ça, une pièce
    # renommée dans le modèle ferait réapparaître la porte du cabanon en
    # silence, et personne ne rouvrirait la liste.
    if exclus:
        vus = {n for o in doc.Objects for n in (o.Name, o.Label)}
        fantomes = sorted(exclus - vus)
        if fantomes:
            raise RuntimeError(
                "pièces à écarter introuvables dans le document : "
                + ", ".join(fantomes))
    return retenus


SCRIPT_BLENDER = r'''
import bpy, json, sys, math

manifeste = sys.argv[sys.argv.index("--") + 1]
sortie = sys.argv[sys.argv.index("--") + 2]
pieces = json.load(open(manifeste, encoding="utf-8"))

bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_vers_lineaire(c):
    """Blender prend la Base Color en LINEAIRE (piege 5 de l'en-tete)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def importer(chemin):
    if hasattr(bpy.ops.wm, "stl_import"):        # Blender 4.x et au-dela
        bpy.ops.wm.stl_import(filepath=chemin)
    else:
        bpy.ops.import_mesh.stl(filepath=chemin)
    return bpy.context.selected_objects[0]


for p in pieces:
    o = importer(p["stl"])
    o.name = p["nom"]
    m = bpy.data.materials.new(name=p["nom"])
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    r, v, b = [srgb_vers_lineaire(c) for c in p["couleur"]]
    bsdf.inputs["Base Color"].default_value = (r, v, b, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    if p["opacite"] < 1.0:
        bsdf.inputs["Alpha"].default_value = p["opacite"]
        m.blend_method = "BLEND"
    o.data.materials.append(m)
    for f in o.data.polygons:
        f.use_smooth = True
    mod = o.modifiers.new("angle", "EDGE_SPLIT")
    mod.split_angle = math.radians(35)

# du millimetre au metre, et on recentre : le visualiseur cadre tout seul.
bpy.ops.object.select_all(action="SELECT")
for o in bpy.context.selected_objects:
    o.scale = (0.001, 0.001, 0.001)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

bpy.ops.export_scene.gltf(filepath=sortie, export_format="GLB",
                          export_apply=True, export_yup=True)
print("GLB ecrit :", sortie)
'''


def exporter(cle, modele, bac, choisis=None, exclus=None, reglages=None):
    import FreeCAD
    import MeshPart

    if not modele.is_file():
        return f"{cle} : modèle introuvable — {modele}", None

    # LA COPIE DOIT EMPORTER SES VOISINS. Un assemblage ne contient pas ses
    # pièces, il les LIE : `AssemblageQuaiV2` pointe sur `Quai.FCStd`,
    # `BrosseV2.FCStd`… du même dossier. Copié seul, il s'ouvre sans erreur et
    # sans un solide — d'où « aucun solide visible à exporter » sur un document
    # où tout est visible et coloré (29/08/2026). On recopie donc tous les
    # `.FCStd` du dossier : les liens sont relatifs, ils se retrouvent.
    for voisin in sorted(modele.parent.glob('*.FCStd')):
        shutil.copy2(voisin, bac / voisin.name)
    doc = FreeCAD.openDocument(str(bac / modele.name))

    # ON RÈGLE, ON NE MODÈLE PAS. Le meuble expose `AnglePorte` dans sa
    # feuille ; le site lui donne une valeur sur SA copie, et le modèle fait
    # le reste. La nuance est tout ce qui sépare « le site choisit une vue »
    # de « le site invente une géométrie ». Un alias inconnu ARRÊTE l'export :
    # une porte restée fermée sans un mot, c'est le défaut qu'on répare.
    if reglages:
        feuilles = [o for o in doc.Objects if o.TypeId == 'Spreadsheet::Sheet']
        for alias, valeur in reglages.items():
            pose = False
            for sh in feuilles:
                try:
                    sh.set(alias, str(valeur))
                    pose = True
                except Exception:
                    continue
            if not pose:
                raise RuntimeError(
                    f"réglage « {alias} » refusé par les {len(feuilles)} "
                    f"feuille(s) de {modele.name}")
        doc.recompute()

    pieces, triangles = [], 0
    dossier = bac / cle
    dossier.mkdir(parents=True, exist_ok=True)
    for o, couleur in solides_a_exporter(doc, choisis, exclus):
        try:
            m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=FLECHE,
                                       AngularDeflection=ANGLE, Relative=False)
        except Exception:
            continue
        if not m.CountFacets:
            continue
        stl = dossier / f'{o.Name}.stl'
        m.write(str(stl))
        triangles += m.CountFacets
        pieces.append({'nom': o.Label or o.Name, 'stl': str(stl),
                       'couleur': list(couleur), 'opacite': 1.0})
    FreeCAD.closeDocument(doc.Name)

    if not pieces:
        return f"{cle} : aucun solide visible à exporter", None

    manifeste = dossier / 'manifeste.json'
    manifeste.write_text(json.dumps(pieces, indent=1), encoding='utf-8')
    script = dossier / '_blender.py'
    script.write_text(SCRIPT_BLENDER, encoding='utf-8')

    SORTIE.mkdir(parents=True, exist_ok=True)
    glb = SORTIE / f'{cle}.glb'
    r = subprocess.run(['blender', '--background', '--factory-startup',
                        '--python', str(script), '--',
                        str(manifeste), str(glb)],
                       capture_output=True, text=True)
    if not glb.is_file():
        bout = (r.stderr or r.stdout).strip().splitlines()[-1:] or ['?']
        return f"{cle} : Blender n'a rien produit — {bout[0][:80]}", None

    ko = glb.stat().st_size // 1024
    alerte = '  ⚠ lourd' if triangles > TRIANGLES_MAX else ''
    dire(f"  {cle:<20} {len(pieces):>3} pièces  {triangles:>6} triangles  "
         f"{ko:>5} Ko{alerte}")
    return None, {'cle': cle, 'pieces': len(pieces), 'triangles': triangles,
                  'octets': glb.stat().st_size}


def main():
    import FreeCADGui
    FreeCADGui.showMainWindow()      # sans elle, pas de ViewObject, pas de couleur

    bac = Path(tempfile.mkdtemp(prefix='exporter_glb_'))
    soucis, faits = [], []
    try:
        for cle, modele, _resume, _page, choisis, exclus, reglages in MODELES:
            try:
                s, info = exporter(cle, modele, bac, choisis, exclus,
                                   reglages)
            except Exception:
                s, info = (f"{cle} : "
                           f"{traceback.format_exc().strip().splitlines()[-1]}"), None
            if s:
                soucis.append(s)
                dire(f"  ÉCHEC  {s}")
            else:
                faits.append(info)
    finally:
        shutil.rmtree(bac, ignore_errors=True)

    total = sum(f['octets'] for f in faits)
    dire("")
    dire(f"{len(faits)}/{len(MODELES)} modèle(s) — {total // 1024} Ko en tout")
    if soucis:
        dire(f"ÉCHEC — {len(soucis)} modèle(s)")
        return 1
    return 0


# PAS de garde `if __name__ == "__main__":` — la console de FreeCAD exécute
# avec un autre `__name__` : le garde ne se déclenche pas, le script ne fait
# RIEN, et le processus sort avec 0.
_code = 1
try:
    _code = main()
except Exception:
    dire("ÉCHEC — exception :\n" + traceback.format_exc())
dire(f"(code {_code})")
raise SystemExit(_code)
