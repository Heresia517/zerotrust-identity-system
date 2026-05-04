#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de présentation PowerPoint pour soutenance Master
Version corrigée (sans erreur XML)
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# ========== CONFIGURATION COULEURS ==========
TITLE_COLOR = RGBColor(0, 51, 102)      # Bleu foncé
ACCENT_COLOR = RGBColor(0, 112, 192)    # Bleu clair
TEXT_COLOR = RGBColor(0, 0, 0)
GOOD_COLOR = RGBColor(0, 153, 0)        # Vert
WARN_COLOR = RGBColor(255, 102, 0)      # Orange

# ========== FONCTIONS ==========
def add_footer(slide, text="TOPAN TOÉ HÉZÉKIAH", slide_num=None):
    """Ajoute un pied de page (texte + numéro)"""
    footer_box = slide.shapes.add_textbox(Inches(0.5), Inches(7), Inches(9), Inches(0.4))
    footer_frame = footer_box.text_frame
    footer_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    footer = footer_frame.paragraphs[0]
    footer.font.size = Pt(10)
    footer.font.color.rgb = RGBColor(128, 128, 128)
    if slide_num is not None:
        footer.text = f"{text}  |  Slide {slide_num}"
    else:
        footer.text = text

def add_bullet_slide(prs, title, bullets, notes=""):
    """Slide avec puces"""
    slide_layout = prs.slide_layouts[1]  # Titre + contenu
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = TITLE_COLOR
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.clear()
    for bullet in bullets:
        p = tf.add_paragraph()
        p.text = bullet
        p.font.size = Pt(18)
        p.space_after = Pt(6)
        if bullet.startswith('   '):
            p.level = 1
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide

def add_two_column_slide(prs, title, left_items, right_items, notes=""):
    slide_layout = prs.slide_layouts[5]  # Titre seulement
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = TITLE_COLOR
    left_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.5), Inches(5))
    right_box = slide.shapes.add_textbox(Inches(5), Inches(1.5), Inches(4.5), Inches(5))
    for tf, items in [(left_box.text_frame, left_items), (right_box.text_frame, right_items)]:
        tf.clear()
        for item in items:
            p = tf.add_paragraph()
            p.text = item
            p.font.size = Pt(16)
            p.space_after = Pt(6)
            if item.startswith('   '):
                p.level = 1
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide

def add_table_slide(prs, title, headers, rows, notes=""):
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = TITLE_COLOR
    rows_count = len(rows) + 1
    cols_count = len(headers)
    left = Inches(0.5)
    top = Inches(1.5)
    width = Inches(9)
    height = Inches(0.5) * rows_count
    table = slide.shapes.add_table(rows_count, cols_count, left, top, width, height).table
    # En-têtes
    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = header
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(14)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT_COLOR
    # Remplir lignes
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i+1, j)
            cell.text = str(val)
            cell.text_frame.paragraphs[0].font.size = Pt(12)
            if "✅" in val:
                cell.text_frame.paragraphs[0].font.color.rgb = GOOD_COLOR
            elif "⚠️" in val:
                cell.text_frame.paragraphs[0].font.color.rgb = WARN_COLOR
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide

def add_title_slide(prs, title, subtitle):
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = TITLE_COLOR
    slide.placeholders[1].text = subtitle
    return slide

def add_image_placeholder_slide(prs, title, description_lines, placeholder_text="[VISUEL : Insérez votre image ici]"):
    """Slide avec un grand rectangle pour image"""
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = TITLE_COLOR
    # Zone de texte descriptive
    desc = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(1.5))
    tf = desc.text_frame
    for line in description_lines:
        p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(16)
        p.space_after = Pt(6)
    # Rectangle pour image
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(3), Inches(9), Inches(2.5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(240, 240, 240)
    shape.line.color.rgb = ACCENT_COLOR
    text_frame = shape.text_frame
    text_frame.text = placeholder_text
    text_frame.paragraphs[0].font.size = Pt(14)
    text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    return slide

def main():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1 : Titre
    add_title_slide(prs,
        "AUTHENTIFICATION DÉCENTRALISÉE",
        "Zero Trust + Blockchain + AES-256\nSécurité avancée pour les systèmes IAM\n\nTOPAN TOÉ HÉZÉKIAH\nMaster Cybersécurité 2024-2025")

    # Slide 2 : Contexte & Problème
    add_bullet_slide(prs, "CONTEXTE & PROBLÈME", [
        "🔴 IAM centralisés = Point de défaillance unique (SPOF)",
        "🔴 Incidents majeurs : SolarWinds (18k organisations), Okta, Colonial Pipeline",
        "🔴 Confiance implicite persistante → mouvements latéraux non détectés",
        "🔴 Stockage centralisé des credentials → cible privilégiée pour les attaquants"
    ], notes="Insister sur les coûts et la fréquence des attaques")

    # Slide 3 : Hypothèses
    add_bullet_slide(prs, "HYPOTHÈSES DE RECHERCHE", [
        "H1 : L’intégration ZTA + Blockchain + chiffrement est techniquement faisable",
        "H2 : La résilience (disponibilité + révocation) est améliorée",
        "H3 : AES-256-GCM garantit confidentialité et intégrité des données",
        "H4 : L’overhead Blockchain reste acceptable (latence ≤ 2 secondes)"
    ], notes="Présenter les 4 hypothèses, elles seront validées plus tard")

    # Slide 4 : Gap scientifique
    add_two_column_slide(prs, "GAP SCIENTIFIQUE",
        ["❌ IAM centralisé : SPOF, confiance implicite",
         "❌ Zéro-Trust seul : pas de décentralisation",
         "❌ Blockchain/DID : pas d’intégration IAM",
         "➡️ AUCUNE solution Keycloak+Blockchain+chiffrement"],
        ["✅ Notre architecture :",
         "   • Keycloak (IAM ZT)",
         "   • Ethereum (registre décentralisé)",
         "   • AES-256-GCM (confidentialité)"],
        notes="Expliquer pourquoi c'est original")

    # Slide 5 : Architecture (avec placeholder pour image)
    add_image_placeholder_slide(prs, "ARCHITECTURE PROPOSÉE – 3 COUCHES",
        ["Couche 1 – IAM Zéro-Trust (Keycloak) : MFA, tokens 5 min",
         "Couche 2 – Registre Blockchain (Ethereum/Solidity) : immuable, vérification",
         "Couche 3 – Chiffrement end-to-end (AES-256-GCM) : confidentialité + tag GCM",
         "🔁 Double validation obligatoire : Keycloak ET Blockchain"],
        "[VISUEL : Figure 1 – Diagramme des trois couches avec flèches]")

    # Slide 6 : Flux authentification
    add_bullet_slide(prs, "FLUX D’AUTHENTIFICATION (DOUBLE VALIDATION)", [
        "1. Utilisateur → Keycloak : login + MFA",
        "2. Keycloak → Smart contract : verifier(adresse_ethereum)",
        "3. Smart contract → Keycloak : true/false",
        "4. Keycloak génère JWT avec claim 'blockchain_verified: true'",
        "5. Accès aux données → déchiffrement AES-256-GCM"
    ], notes="Expliquer que c'est le cœur Zéro-Trust")

    # Slide 7 : Implémentation technique
    add_bullet_slide(prs, "STACK TECHNIQUE (100% OPEN SOURCE)", [
        "🐳 Docker Compose : 6 services (Keycloak, PostgreSQL, Hardhat, Redis, Vault, MinIO)",
        "🔐 Keycloak v23.0.7 – IAM Zéro-Trust",
        "⛓️ Hardhat + Solidity 0.8.19 – smart contract IdentityRegistry",
        "🔒 Python + cryptography (AES-256-GCM) – chiffrement end-to-end",
        "📦 Reproductible : docker compose up"
    ], notes="Montrer la simplicité de déploiement")

    # Slide 8 : Métriques et seuils
    add_table_slide(prs, "PROTOCOLE D’ÉVALUATION – MÉTRIQUES",
        ["Métrique", "Seuil d'acceptabilité"],
        [
            ["Taux détection attaques (TDA)", "≥ 90%"],
            ["Disponibilité sous DoS (DSDOS)", "≥ 80%"],
            ["Temps révocation effectif (TRE)", "≤ 10 min"],
            ["Latence authentification", "≤ 2000 ms"],
            ["Débit (auth/s)", "≥ 10 auth/s"]
        ], notes="Ces seuils viennent des bonnes pratiques")

    # Slide 9 : Résultats sécurité
    add_table_slide(prs, "RÉSULTATS – SÉCURITÉ (4 SCÉNARIOS)",
        ["Scénario", "Taux détection", "Mécanisme"],
        [
            ["A – Rejeu de token", "100% (50/50)", "TTL 5 min + vérif. Blockchain"],
            ["B – DoS (1000 req.)", "86% disponibilité", "Brute-force protection KC"],
            ["C – Falsification JWT", "100% (30/30)", "Signature RS256"],
            ["D – Interception réseau", "0% données lisibles", "AES-256-GCM"]
        ], notes="Souligner le 100% de détection")

    # Slide 10 : Performance
    add_table_slide(prs, "RÉSULTATS – PERFORMANCE",
        ["Mesure", "Système proposé", "Système référence", "Seuil"],
        [
            ["Latence moyenne", "462 ± 31 ms", "134 ± 12 ms", "≤ 2000 ms ✅"],
            ["Overhead Blockchain", "312 ms", "-", "≤ 500 ms ✅"],
            ["Débit max", "16,8 auth/s", "61,7 auth/s", "≥ 10 auth/s ✅"]
        ], notes="L'overhead est acceptable, inférieur à 0,5 seconde")

    # Slide 11 : Résilience
    add_bullet_slide(prs, "RÉSULTATS – RÉSILIENCE", [
        "📊 Disponibilité sous DoS : 86% (≥ 80% ✅)",
        "⏱️ Temps de révocation effectif : < 5 minutes (≤ 10 min ✅)",
        "🛡️ Résistance Sybil : 0/180 identités frauduleuses créées",
        "💾 Compromission base de données : données chiffrées inexploitables"
    ], notes="Comparer avec IAM centralisé qui tombe à 76%")

    # Slide 12 : Validation des hypothèses
    add_table_slide(prs, "VALIDATION DES HYPOTHÈSES",
        ["Hypothèse", "Métrique", "Résultat", "Seuil", "Statut"],
        [
            ["H1 – Faisabilité", "TDA", "100%", "≥90%", "✅ VALIDÉE"],
            ["H2 – Résilience", "DSDOS + TRE", "86% / <5 min", "≥80% / ≤10 min", "✅ VALIDÉE"],
            ["H3 – Confidentialité", "Données lisibles", "0%", "0%", "✅ VALIDÉE"],
            ["H4 – Performance", "Latence", "462 ms", "≤2000 ms", "✅ VALIDÉE"]
        ], notes="Toutes les hypothèses sont confirmées")

    # Slide 13 : Contributions
    add_bullet_slide(prs, "CONTRIBUTIONS", [
        "📚 Scientifiques :",
        "   • Cadre intégrant ZTA (NIST) + Blockchain + chiffrement",
        "   • Identification du gap IAM centralisé ↔ identités décentralisées",
        "🛠️ Pratiques :",
        "   • Prototype open source, conteneurisé, reproductible",
        "   • Smart contract IdentityRegistry testé (8/8 unit tests)",
        "   • Scripts de configuration automatique Keycloak"
    ], notes="Valoriser l'aspect reproductible")

    # Slide 14 : Limites
    add_bullet_slide(prs, "LIMITES (TRANSPARENCE SCIENTIFIQUE)", [
        "⚠️ Keycloak reste un SPOF (décentralisation partielle)",
        "⚠️ Tests sur Hardhat local → latence sous-estimée vs Ethereum mainnet",
        "⚠️ Gestion simplifiée des clés (pas de HSM)",
        "⚠️ Absence de TLS en développement (acceptable pour prototype)",
        "⚠️ Révocation non instantanée : fenêtre de 5 min (durée de vie JWT)"
    ], notes="Assumer ces limites, elles orientent les travaux futurs")

    # Slide 15 : Perspectives
    add_bullet_slide(prs, "PERSPECTIVES D’AMÉLIORATION", [
        "🚀 Court terme : Cache Redis → overhead Blockchain 312 ms → ~10 ms",
        "⚙️ Moyen terme : Hyperledger Fabric → temps déterministes",
        "🔮 Long terme : Self-Sovereign Identity (SSI) + Verifiable Credentials",
        "🏭 Production : HSM/Vault pour clés, TLS 1.3, load balancing"
    ], notes="Montrer la roadmap")

    # Slide 16 : Conclusion
    add_bullet_slide(prs, "CONCLUSION", [
        "✅ Architecture fonctionnelle : Keycloak + Ethereum + AES-256-GCM",
        "✅ 4 hypothèses validées expérimentalement",
        "✅ Taux de détection des attaques = 100%",
        "⚠️ Overhead acceptable (462 ms) – optimisable",
        "🔜 Première étape vers un IAM véritablement décentralisé et souverain"
    ], notes="Terminer sur une note positive mais réaliste")

    # Slide 17 : Questions
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "MERCI"
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = TITLE_COLOR
    slide.placeholders[1].text = "Questions ?\n\nDr. YANOGO K. Jean Hermann\nM. Hamed MANDE"
    slide.notes_slide.notes_text_frame.text = "Préparer des réponses aux questions courantes"

    # Ajout du pied de page sur toutes les slides
    for i, slide in enumerate(prs.slides, start=1):
        add_footer(slide, "TOPAN TOÉ HÉZÉKIAH", slide_num=i)

    # Sauvegarde
    output_path = "presentation_soutenance_amelioree.pptx"
    prs.save(output_path)
    print(f"✅ Présentation générée avec succès : {output_path}")
    print(f"📊 Nombre de slides : {len(prs.slides)}")
    print("🎨 Mise en forme améliorée, notes de présentation et pied de page inclus.")

if __name__ == "__main__":
    main()