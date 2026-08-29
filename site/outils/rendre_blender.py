# -*- coding: utf-8 -*-
"""
rendre_blender.py — une belle image d'un modèle, dans Blender.

    blender --background --factory-startup --python site/outils/rendre_blender.py -- \
        site/contenu/modeles/dust-shoe.glb /tmp/sabot.png

Options après les deux tirets : --taille 1600x1200 --azimut 35 --hauteur 25
--echantillons 128 --fond blanc|transparent --sol oui|non

TROISIÈME CHAÎNE, ET ELLE NE REMPLACE NI L'UNE NI L'AUTRE.
`rendre_3d.py` prend la vue 3D de FreeCAD : instantané, plat, gratuit — c'est
ce qu'il faut pour une vignette de page projet. `exporter_glb.py` fabrique
l'objet qu'on fait tourner dans le navigateur. Celui-ci fait une IMAGE
SOIGNÉE : ombres portées, matières, lumière d'atelier. Plus lent, à réserver
à ce qu'on montre en grand.

IL PART D'UN GLB, PAS D'UN .FCStd, et c'est volontaire : `exporter_glb.py`
sait déjà mailler et coloriser depuis FreeCAD, et refaire ce travail ici
aurait été une seconde source de vérité. La procédure est donc en deux
temps — le GLB, puis l'image.

CE QUI EST DÉJÀ PAYÉ AILLEURS ET QU'ON N'A PAS À REPAYER : les couleurs
viennent du document FreeCAD (un `.FCStd` écrit sans interface sort GRIS), et
la conversion sRGB → linéaire est faite par `exporter_glb.py`. Ici les
matières arrivent déjà justes avec le glTF.
"""
import math
import os
import sys

import bpy
from mathutils import Vector


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(a) < 2:
        print("usage : … --python rendre_blender.py -- entree.glb sortie.png [options]")
        sys.exit(2)
    o = {"taille": "1600x1200", "azimut": "35", "hauteur": "25",
         "echantillons": "128", "fond": "blanc", "sol": "oui",
         "film": "standard"}
    reste = a[2:]
    for i in range(0, len(reste) - 1, 2):
        o[reste[i].lstrip("-")] = reste[i + 1]
    return a[0], a[1], o


def scene_vide():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def emprise():
    """Boîte englobante de tout ce qui est visible, en coordonnées monde."""
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector((min(lo[i], p[i]) for i in range(3)))
            hi = Vector((max(hi[i], p[i]) for i in range(3)))
    return lo, hi


def poser_camera(lo, hi, azimut, hauteur):
    """Cadre l'objet SANS `camera_to_view_selected`, qui exige une vue 3D.

    En arrière-plan il n'y en a pas — l'appeler lève « context is incorrect ».
    On calcule donc : rayon de la sphère englobante, puis distance telle que
    la sphère tienne dans le champ, avec une marge.
    """
    centre = (lo + hi) / 2
    rayon = max((hi - lo).length / 2, 1e-6)
    cam = bpy.data.cameras.new("Camera")
    cam.lens = 50
    obj = bpy.data.objects.new("Camera", cam)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.scene.camera = obj

    a, h = math.radians(azimut), math.radians(hauteur)
    direction = Vector((math.cos(h) * math.cos(a), math.cos(h) * math.sin(a),
                        math.sin(h)))
    champ = 2 * math.atan(cam.sensor_width / (2 * cam.lens))
    distance = rayon / math.sin(champ / 2) * 1.12
    obj.location = centre + direction * distance
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
    return centre, rayon


def lumieres(centre, rayon):
    """Trois sources : la clé, le déboucheur, le contre-jour.

    Pas d'image d'environnement : un HDR pèse 1 à 2 Mo, il faudrait le
    versionner, et trois surfaces suffisent largement pour une pièce.
    """
    def source(nom, position, energie, taille):
        d = bpy.data.lights.new(nom, type="AREA")
        d.energy = energie
        d.size = taille
        o = bpy.data.objects.new(nom, d)
        o.location = centre + Vector(position) * rayon
        o.rotation_quaternion = (centre - o.location).to_track_quat("-Z", "Y")
        o.rotation_mode = "QUATERNION"
        bpy.context.scene.collection.objects.link(o)

    # Les énergies sont proportionnelles au CARRÉ du rayon : sans ça, le même
    # réglage brûle une pièce de 8 cm et laisse un cabanon de 2 m dans le noir.
    e = (rayon ** 2) * 12
    source("Cle", (1.4, -1.6, 1.9), e * 3.0, rayon * 2.2)
    source("Debouchage", (-2.0, -0.8, 0.7), e * 1.0, rayon * 2.6)
    source("ContreJour", (-0.6, 2.2, 1.4), e * 1.6, rayon * 1.8)

    return monde_a_deux_visages()


def monde_a_deux_visages(fond=(1.0, 1.0, 1.0)):
    """Fond CLAIR pour l'appareil, ambiance NEUTRE pour l'éclairage.

    Dans Cycles le monde fait les deux à la fois : ce qu'on voit derrière
    l'objet, ET la lumière d'ambiance qui déboucher les ombres. Un monde blanc
    donne donc un fond blanc mais délave la pièce ; un monde gris éclaire bien
    mais l'image sort sur fond gris — c'est ce que rendait la première version.
    On les sépare par un `Light Path` : les rayons venus de l'APPAREIL voient
    le fond choisi, tous les autres voient le gris qui éclaire.
    """
    monde = bpy.data.worlds.new("Monde")
    monde.use_nodes = True
    a = monde.node_tree
    for n in list(a.nodes):
        a.nodes.remove(n)
    sortie = a.nodes.new("ShaderNodeOutputWorld")
    melange = a.nodes.new("ShaderNodeMixShader")
    chemin = a.nodes.new("ShaderNodeLightPath")
    vu = a.nodes.new("ShaderNodeBackground")       # ce que l'appareil voit
    ambiance = a.nodes.new("ShaderNodeBackground")  # ce qui éclaire
    vu.inputs[0].default_value = (*fond, 1)
    vu.inputs[1].default_value = 1.0
    ambiance.inputs[0].default_value = (.55, .57, .60, 1)
    ambiance.inputs[1].default_value = 0.45
    a.links.new(chemin.outputs["Is Camera Ray"], melange.inputs[0])
    a.links.new(ambiance.outputs[0], melange.inputs[1])
    a.links.new(vu.outputs[0], melange.inputs[2])
    a.links.new(melange.outputs[0], sortie.inputs[0])
    bpy.context.scene.world = monde
    return monde


def sol(lo, centre, rayon, fond):
    """Un plan qui NE REÇOIT QUE L'OMBRE.

    SANS MATIÈRE, ET C'EST TOUT LE POINT. Un `is_shadow_catcher` ne montre
    que l'ombre portée, le fond passe au travers — mais si on lui pose une
    matière, elle est ÉCLAIRÉE et c'est elle qu'on voit : le fond blanc
    ressortait gris clair, dégradé par les trois sources. Mesuré à la
    première mouture. Sans matière, l'objet cesse de flotter et le fond
    reste celui qu'on a demandé."""
    bpy.ops.mesh.primitive_plane_add(size=rayon * 14,
                                     location=(centre.x, centre.y, lo.z))
    bpy.context.object.is_shadow_catcher = True


def main():
    entree, sortie, o = args()
    if not os.path.isfile(entree):
        print("rendre_blender : introuvable —", entree)
        sys.exit(1)

    scene_vide()
    bpy.ops.import_scene.gltf(filepath=entree)
    lo, hi = emprise()
    if lo.x > hi.x:
        print("rendre_blender : aucun maillage dans", entree)
        sys.exit(1)

    centre, rayon = poser_camera(lo, hi, float(o["azimut"]), float(o["hauteur"]))
    lumieres(centre, rayon)
    if o["fond"] not in ("blanc", "transparent"):
        h = o["fond"].lstrip("#")
        monde_a_deux_visages(tuple(
            (int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)))
    if o["sol"] != "non":
        sol(lo, centre, rayon, o["fond"])

    sc = bpy.context.scene

    # LA TRANSFORMATION DE VUE, ET C'EST LE PIÈGE QUI M'A COÛTÉ TROIS RENDUS.
    # Blender applique AgX par défaut : un film qui compresse les hautes
    # lumières comme une pellicule. Superbe pour une scène éclairée, désastreux
    # pour une fiche produit — un fond BLANC PUR en ressort à 196,196,196,
    # mesuré au pixel. On a d'abord accusé le plan d'ombre, puis le monde ;
    # c'était le tone mapping. « Standard » rend ce qu'on a demandé.
    sc.view_settings.view_transform = (
        "AgX" if o.get("film") == "agx" else "Standard")

    sc.render.engine = "CYCLES"
    sc.cycles.samples = int(o["echantillons"])
    sc.cycles.use_denoising = True
    # GPU si la machine en a un : mesuré sur la RX 7600M XT, backend HIP.
    # On retombe sur le processeur sans rien dire d'autre qu'une ligne.
    try:
        cp = bpy.context.preferences.addons["cycles"].preferences
        cp.compute_device_type = "HIP"
        cp.get_devices()
        gpus = [d for d in cp.devices if d.type != "CPU"]
        for d in cp.devices:
            d.use = (d.type != "CPU")
        sc.cycles.device = "GPU" if gpus else "CPU"
        print("rendu sur", sc.cycles.device, [d.name for d in gpus] or "(processeur)")
    except Exception as e:
        sc.cycles.device = "CPU"
        print("rendu sur le processeur :", e)

    larg, _, haut = o["taille"].partition("x")
    sc.render.resolution_x, sc.render.resolution_y = int(larg), int(haut)
    sc.render.film_transparent = (o["fond"] == "transparent")
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = sortie
    bpy.ops.render.render(write_still=True)
    print("écrit :", sortie, os.path.getsize(sortie), "octets")


main()
