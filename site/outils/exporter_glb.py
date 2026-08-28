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

# (clé, modèle FreeCAD, ce que la page en dit, page du site)
#
# Un modèle dont le document s'ouvre avec des dizaines d'objets visibles qui
# ne composent rien ne donne pas un GLB montrable : le magasin ATC est dans
# ce cas (216 objets visibles sur 516), il est ÉCARTÉ comme il l'est déjà
# dans rendre_3d.py. Ce n'est pas une régression, c'est le même constat.
MODELES = [
    ('attache-gouttiere',
     Path.home() / 'Projets/realisations/attache-gouttiere/AttacheGouttiere80.FCStd',
     "Collier de descente Ø 80, deux pièces imprimées et un insert récupéré.",
     'projets/attache-gouttiere.html'),
    ('dust-shoe',
     Path.home() / 'Projets/machine/dust-shoe/fcstd/sabot_v2.FCStd',
     "Le sabot d'aspiration de la PrintNC, semelle et quai aimanté.",
     'projets/dust-shoe.html'),
    ('tonnelle-jasmin',
     Path.home() / 'Projets/realisations/tonnelle-jasmin/Tonnelle.FCStd',
     "La tonnelle montée : poteaux, sablières, chevrons et plots.",
     'projets/tonnelle-jasmin.html'),
    ('meuble-balais',
     Path.home() / 'Projets/realisations/meuble-balais/MeubleABalais.FCStd',
     "L'armoire de jardin, bardage et toit.",
     'projets/meuble-balais.html'),
]

_lignes = []


def dire(texte):
    _lignes.append(texte)
    print(texte, flush=True)
    JOURNAL.write_text("\n".join(_lignes) + "\n", encoding='utf-8')


def solides_visibles(doc):
    """Les solides de tête effectivement affichés, avec leur couleur.

    « De tête » = que rien d'autre ne consomme : sans ce filtre on exporte
    aussi les étapes intermédiaires d'un PartDesign, et le GLB pèse trois
    fois trop lourd pour la même image."""
    retenus = []
    for o in doc.Objects:
        forme = getattr(o, 'Shape', None)
        if forme is None or not forme.Solids:
            continue
        if [p for p in o.InList if hasattr(p, 'Shape')]:
            continue
        vo = getattr(o, 'ViewObject', None)
        if vo is None or not getattr(vo, 'Visibility', False):
            continue
        couleur = tuple(getattr(vo, 'ShapeColor', (0.72, 0.72, 0.74))[:3])
        retenus.append((o, couleur, getattr(vo, 'Transparency', 0)))
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


def exporter(cle, modele, bac):
    import FreeCAD
    import MeshPart

    if not modele.is_file():
        return f"{cle} : modèle introuvable — {modele}", None

    copie = bac / modele.name
    shutil.copy2(modele, copie)
    doc = FreeCAD.openDocument(str(copie))

    pieces, triangles = [], 0
    dossier = bac / cle
    dossier.mkdir(parents=True, exist_ok=True)
    for o, couleur, transp in solides_visibles(doc):
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
                       'couleur': list(couleur),
                       'opacite': 1.0 - transp / 100.0})
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
        for cle, modele, _resume, _page in MODELES:
            try:
                s, info = exporter(cle, modele, bac)
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
