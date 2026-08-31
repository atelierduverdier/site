#!/usr/bin/env python3
# =========================================================================
# pictos.py — le jeu de pictogrammes des cartes du site
# =========================================================================
# UN SEUL STYLE, ET UN SEUL ENDROIT OÙ IL EST ÉCRIT.
#
# Les cartes portaient des émojis : 🔥 📐 🪚 ✂️ 🧮 ⚙️ sur l'accueil,
# 🌧️ 🔩 🌿 🧹 🪟 🌀 sur les projets, et huit autres dispersés dans les
# fiches. Trois défauts, relevés par Christophe le 31/08/2026 :
#
#   * ils ne sont pas d'un même style — un émoji est dessiné par le
#     système, et ni Noto, ni Apple, ni Segoe ne s'accordent sur le trait,
#     l'épaisseur ni même le nombre de couleurs ;
#   * ils sont EN COULEUR, dans une page qui n'en a que deux ;
#   * ils ne suivent ni le thème sombre ni l'accent de la maison.
#
# D'où ce jeu au trait : un même `viewBox` de 24, une même épaisseur, des
# bouts et des raccords ronds, et `currentColor` partout — la couleur vient
# donc du CSS (`.carte .ci`, en encre orange sur la pastille pâle) et suit
# le thème sans qu'on retouche un seul dessin.
#
# La règle de la maison s'applique ici comme ailleurs : un picto s'écrit
# UNE fois. « L'aspiration » sert au sabot sur trois pages, « l'engrenage »
# à la config PrintNC et aux volets — un seul `d`, trois emplois.
#
# Une clé inconnue ARRÊTE la génération : une carte sans son picto n'est
# pas une carte dégradée, c'est une carte dont le carré reste vide.
# =========================================================================

import re
import sys

# Les attributs communs à TOUS les pictos. Écrits une fois : c'est ce qui
# garantit que le jeu reste homogène, quoi qu'on ajoute plus tard.
GABARIT = ('<svg class="picto" viewBox="0 0 24 24" fill="none" '
           'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true" focusable="false">'
           '{corps}</svg>')

# clé -> les tracés du dessin. Rien d'autre : ni couleur, ni taille, ni
# épaisseur — tout cela vit dans GABARIT et dans la feuille de style.
DESSINS = {
    # --- Les logiciels (accueil) ----------------------------------------
    # Une tête laser au-dessus d'une surface BOMBÉE — la raison d'être du
    # greffon, pas une machine à graver du plat. Deux formes essayées avant :
    # faisceau convergent (ça faisait une coupe de trophée) puis surface
    # plane (une lampe de bureau). C'est la planche de contrôle plus bas qui
    # les a départagées, jamais la lecture du `d`.
    'laser': ('<rect x="6.5" y="3" width="11" height="6" rx="2"/>'
              '<circle cx="12" cy="6" r="1.5"/>'
              '<path d="M12 9v6"/>'
              '<path d="M4 19.5h16"/>'),
    # Un parcours d'outil : segments orthogonaux, départ et arrivée marqués.
    'parcours': ('<path d="M4 19h4v-8h6V6h6"/>'
                 '<circle cx="4" cy="19" r="1.5"/><circle cx="20" cy="6" r="1.5"/>'),
    # Un panneau débité en coupes guillotine.
    'debit': ('<rect x="3" y="4" width="18" height="16" rx="2"/>'
              '<path d="M3 12h18"/><path d="M12 4v8"/><path d="M16 12v8"/>'),
    # La découpe. Le chariot du traceur avec sa lame a été dessiné d'abord —
    # mais à 21 px il ne se distinguait plus de l'outil pendu du magasin ATC,
    # même triangle sur la même tige. Deux cartes du site auraient porté le
    # même picto pour deux machines différentes.
    'traceur': ('<circle cx="6" cy="6" r="2.4"/><circle cx="6" cy="18" r="2.4"/>'
                '<path d="M20 4 8.1 16.4"/><path d="M20 20 8.1 7.6"/>'),
    # Un cadran d'aiguille : la vitesse, justement.
    'vitesse': ('<path d="M4 17a8 8 0 1 1 16 0"/>'
                '<path d="m12 17 4.2-4.6"/><circle cx="12" cy="17" r="1.2"/>'
                '<path d="M4.9 12.3 6.4 13.2"/><path d="M12 8.8V7"/>'
                '<path d="m19.1 12.3-1.5.9"/>'),
    # La roue dentée : la configuration de la machine, et ce qui se déduit
    # tout seul d'une saisie (volets).
    'engrenage': ('<circle cx="12" cy="12" r="3"/>'
                  '<circle cx="12" cy="12" r="7.2"/>'
                  '<path d="M12 4.8V3"/><path d="M12 19.2V21"/>'
                  '<path d="M4.8 12H3"/><path d="M19.2 12H21"/>'
                  '<path d="M17.1 6.9 18.4 5.6"/><path d="M5.6 18.4 6.9 17.1"/>'
                  '<path d="M17.1 17.1 18.4 18.4"/><path d="M5.6 5.6 6.9 6.9"/>'),
    # Un tableur : la grille et sa ligne d'en-tête — ce qui est SAISI.
    'tableur': ('<rect x="3" y="4" width="18" height="16" rx="2"/>'
                '<path d="M3 9h18"/><path d="M3 14.5h18"/><path d="M9 9v11"/>'),

    # --- Les projets ------------------------------------------------------
    # Une descente de gouttière prise dans son collier, oreilles comprises.
    'descente': ('<path d="M9 3v18"/><path d="M15 3v18"/>'
                 '<rect x="6.5" y="8.5" width="11" height="5.5" rx="1.2"/>'
                 '<path d="M3 11.2h3.5"/><path d="M17.5 11.2H21"/>'),
    # Un outil pendu dans sa fourche : le changeur d'outil automatique.
    # La bille elle-même a été essayée trois fois — dans son alésage, dans
    # son chanfrein, dans un V — et les trois donnaient un bonhomme ou une
    # serrure. Le magasin se reconnaît, la bille non.
    'outil': ('<path d="M4 5h16"/>'
              '<path d="M9 5v3"/><path d="M15 5v3"/>'
              '<path d="M8.2 8h7.6l-2.2 6h-3.2L8.2 8Z"/>'
              '<path d="M12 14v6"/>'),
    # Une tonnelle : deux pieds, une arche, ses traverses.
    'tonnelle': ('<path d="M4 21V10a8 8 0 0 1 16 0v11"/>'
                 '<path d="M4.4 13.5h15.2"/><path d="M4 17.5h16"/>'),
    # Une armoire de jardin : porte latérale, étagères, et le compartiment
    # pleine hauteur devant.
    'armoire': ('<rect x="3.5" y="3" width="17" height="18" rx="2"/>'
                '<path d="M14 3v18"/><path d="M3.5 9.5H14"/><path d="M3.5 15H14"/>'
                '<path d="M12.4 12.5v1.6"/>'),
    # Un volet à deux battants.
    'volet': ('<rect x="3" y="4" width="18" height="16" rx="1.5"/>'
              '<path d="M12 4v16"/>'
              '<path d="M6 8h3"/><path d="M6 12h3"/><path d="M6 16h3"/>'
              '<path d="M15 8h3"/><path d="M15 12h3"/><path d="M15 16h3"/>'),
    # Une buse d'aspiration et son conduit.
    'aspiration': ('<path d="M9.8 4.5v8"/><path d="M14.2 4.5v8"/>'
                   '<path d="M9.8 7h4.4"/><path d="M9.8 9.7h4.4"/>'
                   '<path d="M9.2 12.5h5.6l3.2 6.6H6l3.2-6.6Z"/>'
                   '<path d="M3.5 20.8h17"/>'),
    # Une brosse : le dos et les poils.
    'brosse': ('<rect x="3" y="5.5" width="18" height="5" rx="1.5"/>'
               '<path d="M6 10.5V18"/><path d="M9 10.5V18"/><path d="M12 10.5V18"/>'
               '<path d="M15 10.5V18"/><path d="M18 10.5V18"/>'),
    # Une ancre : la pièce qui ne se dépose jamais.
    'ancre': ('<circle cx="12" cy="4.5" r="2"/>'
              '<path d="M12 6.5V21"/><path d="M8 10h8"/>'
              '<path d="M4 13.5a8 8 0 0 0 16 0"/>'),

    # --- Ce que le bois a démenti (fiche LaserAtelier) --------------------
    # Un nuancier : trois plages de densité croissante.
    'nuancier': ('<rect x="3" y="6" width="5.5" height="12" rx="1.2"/>'
                 '<rect x="9.25" y="6" width="5.5" height="12" rx="1.2"/>'
                 '<rect x="15.5" y="6" width="5.5" height="12" rx="1.2"/>'
                 '<path d="M9.25 12h5.5"/>'
                 '<path d="M15.5 9h5.5"/><path d="M15.5 12h5.5"/>'
                 '<path d="M15.5 15h5.5"/>'),
    # Un dégradé, rendu par la densité des traits — pas par un aplat, pour
    # rester au trait comme le reste du jeu.
    'degrade': ('<rect x="3" y="4" width="18" height="16" rx="2"/>'
                '<path d="M6 6v12"/><path d="M10 6v12"/><path d="M13 6v12"/>'
                '<path d="M15.4 6v12"/><path d="M17.3 6v12"/><path d="M18.8 6v12"/>'),
    # Un chronomètre : le temps de séjour.
    'chrono': ('<circle cx="12" cy="13.5" r="7.5"/>'
               '<path d="M12 9.5v4l2.4 1.8"/>'
               '<path d="M9.7 2.5h4.6"/><path d="M12 2.5V6"/>'),
    # L'écoute : ce que la tête a dit avant que rien ne se voie.
    'ecoute': ('<circle cx="6" cy="12" r="1.8"/>'
               '<path d="M10.5 8.2a6 6 0 0 1 0 7.6"/>'
               '<path d="M14.4 5.2a10.5 10.5 0 0 1 0 13.6"/>'),

    # --- Trois choses vérifiées (fiche visualiseur) -----------------------
    # Une balance : la licence, pesée avant d'être codée.
    'balance': ('<path d="M12 4.5V21"/><path d="M7.5 21h9"/><path d="M4.5 8h15"/>'
                '<path d="M4.5 8 2 13.5h5L4.5 8Z"/>'
                '<path d="M19.5 8 17 13.5h5L19.5 8Z"/>'),
    # Le sens interdit : jamais « -n 0 ».
    'interdit': ('<circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/>'),
    # Une corbeille : le fichier de paramètres jetable.
    'corbeille': ('<path d="M4 6.5h16"/><path d="M10 4h4"/>'
                  '<path d="m6 6.5 1 13.5h10l1-13.5"/>'
                  '<path d="M10.4 10.5v5.5"/><path d="M13.6 10.5v5.5"/>'),
}


def picto(cle: str, nom: str = '?') -> str:
    """Le SVG en ligne d'un picto. Une clé inconnue arrête la génération."""
    if cle not in DESSINS:
        sys.exit(f"pictos : {nom} demande le picto « {cle} », qui n'existe "
                 f"pas. Connus : {', '.join(sorted(DESSINS))}.")
    return GABARIT.format(corps=DESSINS[cle])


def injecter(corps: str, nom: str) -> str:
    """Remplace les `{{ico:cle}}` par leur dessin, en ligne dans la page.

    En ligne et non en `<img>` : c'est `currentColor` qui donne sa teinte
    au trait, donc le picto suit le bouton de thème. Chargé en image, il
    resterait figé sur la couleur écrite dans le fichier.
    """
    if '{{ico:' not in corps:
        return corps
    for cle in sorted(set(re.findall(r'\{\{ico:([\w-]+)\}\}', corps))):
        corps = corps.replace('{{ico:' + cle + '}}', picto(cle, nom))
    reste = re.findall(r'\{\{ico:[^}]*\}\}', corps)
    if reste:
        sys.exit(f"pictos : {nom} — marque non résolue : {reste[0]}")
    return corps


if __name__ == '__main__':
    # Une planche de contrôle, pour regarder le jeu ENSEMBLE : c'est côte
    # à côte qu'un dessin trop chargé ou trop maigre se voit, jamais seul.
    cases = '\n'.join(
        f'<figure><span class="ci">{picto(c)}</span><figcaption>{c}</figcaption></figure>'
        for c in sorted(DESSINS))
    print(f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Pictos de l'Atelier du Verdier</title>
<link rel="stylesheet" href="../kit/verdier.css">
<style>body{{padding:40px}}
.jeu{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:18px}}
figure{{margin:0;text-align:center}}
.ci{{width:34px;height:34px;border-radius:9px;background:var(--orange-soft);
  color:var(--orange-encre);display:grid;place-items:center;margin:0 auto 6px}}
.ci svg{{width:21px;height:21px;display:block}}
figcaption{{font-size:.8rem;color:var(--fg-2)}}</style></head><body>
<h1>{len(DESSINS)} pictos</h1><div class="jeu">
{cases}
</div></body></html>""")
