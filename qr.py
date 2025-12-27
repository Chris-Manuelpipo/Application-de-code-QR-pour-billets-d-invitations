#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
import qrcode
from PIL import Image

# ============= DONNÉES DES INVITÉS =============
tables_data = {
    1: {"nom": "Excellence", "invites": [
        "MONSIEUR ETCHOME HENRI BLAISE ET MADAME",
        "MADEMOISELLE DIELE AUDREY KHAREL",
        "MADAME NGANDO JACQUIS",
        "MADAME VEUVE EPOUNDE CHARLOTTE",
        "MADAME VEUVE MISSE CELESTINE",
        "MONSIEUR ANEURIN MBUGE ET MADAME",
        "SISTER CAROLINE (VOPS)",
        "SA MAJESTE EBANG PAUL"
    ]},
    2: {"nom": "Honneur", "invites": [
        "MONSIEUR DOH JEROME PENBAGA ET MADAME",
        "MONSIEUR FONGOD EDWIN ET MADAME",
        "SENATOR WANLO ET MADAME",
        "MONSIEUR MPOLOMENA BLAISE ET MADAME",
        "MONSIEUR TAM PATRICE ET MADAME",
        "MADAME KEBILA NYONGLEMA SAMA HENSLA ET MONSIEUR",
    ]}
}

# ============= TEMPLATE LATEX =============
LATEX_TEMPLATE = r"""
\documentclass[11pt]{article}
\usepackage[margin=1.5cm]{geometry}
\usepackage{graphicx}
\usepackage{fancyhdr}
\usepackage{xcolor}

\pagestyle{empty}

\begin{document}

\begin{center}
    \vspace*{2cm}
    
    {\Large \textbf{INVITATION OFFICIELLE}}
    
    \vspace{1cm}
    
    {\large \textit{Gala 2025}}
    
    \vspace{2cm}
    
    \hrule
    
    \vspace{1cm}
    
    {\Large \textbf{{{GUEST_NAME}}}}
    
    \vspace{0.5cm}
    
    {\large Table: {{TABLE_NUMBER}}}
    
    {\large \textit{({{TABLE_NAME}})}}
    
    \vspace{2cm}
    
    \includegraphics[width=6cm]{{{QR_CODE_PATH}}}
    
    \vspace{1cm}
    
    {\small Code: {{QR_ID}}}
    
    \vspace{2cm}
    
    \hrule
    
    \vspace{1cm}
    
    {\small \textit{Merci de présenter ce billet à l'entrée}}

\end{center}

\end{document}
"""

# ============= CLASSE DE GESTION =============
class TicketGenerator:
    def __init__(self, event_name="event_20250124"):
        self.event_name = event_name
        self.event_dir = Path(event_name)
        self.qr_dir = self.event_dir / "qrcodes"
        self.pdf_dir = self.event_dir / "pdfs"
        self.data_file = self.event_dir / "tickets_data.json"
        
        # Créer les dossiers
        self.qr_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        self.tickets_data = {}
    
    def generate_qr_code(self, qr_content, qr_id):
        """Génère une image QR code en PNG"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = self.qr_dir / f"{qr_id}.png"
        img.save(qr_path)
        
        return str(qr_path)
    
    def generate_latex_pdf(self, guest_name, table_number, table_name, qr_id, qr_path):
        """Génère un PDF à partir du template LaTeX"""
        # Remplacer les variables dans le template
        latex_content = LATEX_TEMPLATE
        latex_content = latex_content.replace("{{GUEST_NAME}}", guest_name)
        latex_content = latex_content.replace("{{TABLE_NUMBER}}", str(table_number))
        latex_content = latex_content.replace("{{TABLE_NAME}}", table_name)
        latex_content = latex_content.replace("{{QR_ID}}", qr_id)
        latex_content = latex_content.replace("{{QR_CODE_PATH}}", qr_path)
        
        # Créer un nom de fichier sûr
        safe_name = guest_name.replace(" ", "_").replace("/", "_")[:50]
        tex_file = self.event_dir / f"{safe_name}_{qr_id[:8]}.tex"
        
        # Écrire le fichier LaTeX
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Compiler avec pdflatex
        try:
            result = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', '-output-directory', 
                 str(self.pdf_dir), str(tex_file)],
                capture_output=True,
                timeout=10
            )
            
            # Vérifier si le PDF a été créé
            pdf_file = self.pdf_dir / f"{safe_name}_{qr_id[:8]}.pdf"
            if pdf_file.exists():
                print(f"✓ PDF généré: {safe_name}_{qr_id[:8]}.pdf")
            else:
                print(f"✗ PDF non généré pour {guest_name}")
                print(f"  stdout: {result.stdout.decode('utf-8', errors='ignore')[-500:]}")
                print(f"  stderr: {result.stderr.decode('utf-8', errors='ignore')[-500:]}")
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Erreur LaTeX pour {guest_name}: {e}")
            print(f"  {e.stderr.decode('utf-8', errors='ignore')}")
        except FileNotFoundError:
            print("✗ pdflatex non trouvé. Installez texlive-latex-base")
            return False
        finally:
            # Nettoyer les fichiers temporaires dans event_dir ET pdf_dir
            if tex_file.exists():
                tex_file.unlink()
            
            # Nettoyer dans le dossier d'événement
            for ext in ['.aux', '.log']:
                temp_file = self.event_dir / f"{safe_name}_{qr_id[:8]}{ext}"
                if temp_file.exists():
                    temp_file.unlink()
            
            # Nettoyer dans le dossier des PDFs
            for ext in ['.aux', '.log']:
                temp_file = self.pdf_dir / f"{safe_name}_{qr_id[:8]}{ext}"
                if temp_file.exists():
                    temp_file.unlink()
        
        return True
    
    def generate_all_tickets(self):
        """Génère tous les billets"""
        print(f"\n🎫 Génération des billets pour {self.event_name}\n")
        
        total = sum(len(v["invites"]) for v in tables_data.values())
        current = 0
        
        for table_number, table_info in tables_data.items():
            table_name = table_info["nom"]
            
            for guest_name in table_info["invites"]:
                current += 1
                print(f"[{current}/{total}] Traitement: {guest_name}")
                
                # Générer un ID unique
                qr_id = str(uuid.uuid4())
                
                # Créer le contenu du QR code (format structuré)
                qr_content = f"TABLE:{table_number}|INVITE:{guest_name}|ID:{qr_id}"
                
                # Générer l'image QR
                qr_path = self.generate_qr_code(qr_content, qr_id)
                
                # Générer le PDF
                self.generate_latex_pdf(guest_name, table_number, table_name, qr_id, qr_path)
                
                # Enregistrer les données
                self.tickets_data[qr_id] = {
                    "id": qr_id,
                    "nom": guest_name,
                    "table": table_number,
                    "table_name": table_name,
                    "generated_at": datetime.now().isoformat()
                }
        
        # Sauvegarder les données en JSON
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tickets_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ {len(self.tickets_data)} billets générés avec succès!")
        print(f"📁 Dossier: {self.event_dir.absolute()}")
        print(f"📄 Données: {self.data_file}")


# ============= EXÉCUTION =============
if __name__ == "__main__":
    generator = TicketGenerator(event_name="event_20250124")
    generator.generate_all_tickets()