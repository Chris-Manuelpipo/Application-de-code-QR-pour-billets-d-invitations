#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de synchronisation: injecte les données JSON générées dans le HTML
Lancez-le APRÈS avoir exécuté qr.py
"""

import json
import re
from pathlib import Path

def sync_html_with_json(event_dir="event_20250124", html_file="index.html"):
    """
    Injecte les données du fichier JSON dans le HTML
    """
    
    # 1. Lire les données JSON générées
    json_path = Path(event_dir) / "tickets_data.json"
    
    if not json_path.exists():
        print(f"❌ Fichier non trouvé: {json_path}")
        print("   Exécutez d'abord: python qr.py")
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        tickets_data = json.load(f)
    
    print(f"✅ {len(tickets_data)} billets lus depuis {json_path}")
    
    # 2. Lire le HTML
    html_path = Path(html_file)
    if not html_path.exists():
        print(f"❌ Fichier HTML non trouvé: {html_file}")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 3. Créer le code JavaScript pour injecter les données
    js_data = f"const TICKETS_DATA = {json.dumps(tickets_data)};"
    
    # 4. Remplacer la ligne existante
    # On cherche: const TICKETS_DATA = {...};
    pattern = r'const TICKETS_DATA = \{[^}]*(?:\{[^}]*\}[^}]*)*\};'
    
    if re.search(pattern, html_content):
        html_content = re.sub(pattern, js_data, html_content, count=1, flags=re.DOTALL)
        print(f"✅ Données injectées dans {html_file}")
    else:
        print(f"⚠️  Impossible de trouver TICKETS_DATA dans le HTML")
        print("   Vérifiez que la ligne 'const TICKETS_DATA = {...};' existe")
        return False
    
    # 5. Sauvegarder le HTML modifié
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 6. Afficher les statistiques
    tables = {}
    for ticket in tickets_data.values():
        table = ticket['table']
        if table not in tables:
            tables[table] = []
        tables[table].append(ticket['nom'])
    
    print(f"\n📊 Résumé:")
    for table_num in sorted(tables.keys()):
        names = tables[table_num]
        print(f"   Table {table_num}: {len(names)} invités")
    
    print(f"\n✅ Synchronisation réussie!")
    print(f"   Vous pouvez maintenant redéployer l'app")
    
    return True


if __name__ == "__main__":
    import sys
    
    event_dir = "event_20250124"
    html_file = "index.html"
    
    if len(sys.argv) > 1:
        event_dir = sys.argv[1]
    if len(sys.argv) > 2:
        html_file = sys.argv[2]
    
    sync_html_with_json(event_dir, html_file)