import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import time
import random
from urllib.parse import urljoin
from datetime import datetime
import hashlib
import os
import logging
from supabase_client import SupabaseClient  # Notre client personnalisé

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CourirScraper:
    def __init__(self):
        self.supabase = SupabaseClient()
        self.session = self.create_session()
        
    def create_session(self):
        """Créer une session requests avec headers réalistes"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        })
        return session

    def clean_price(self, price_text):
        """Nettoyer et convertir les prix"""
        if not price_text or pd.isna(price_text):
            return None
        try:
            price_str = str(price_text)
            cleaned = price_str.replace('€', '').replace(' ', '').strip()
            cleaned = cleaned.replace(',', '.')
            price_match = re.search(r'(\d+\.?\d*)', cleaned)
            return float(price_match.group(1)) if price_match else None
        except (ValueError, TypeError):
            return None

    def generate_description(self, product_data):
        """Générer une description automatique"""
        name = product_data.get('name', 'Produit')
        brand = product_data.get('brand', 'Marque')
        price = product_data.get('base_price', 0)
        
        description = f"{brand} {name}. Chaussure de qualité supérieure."
        if price > 0:
            description += f" Prix: {price}€."
        
        features = [
            "Semelle confortable pour un usage quotidien.",
            "Design moderne et tendance.",
            "Matériaux de haute qualité.",
            "Parfait pour le sport et le casual."
        ]
        
        description += " " + " ".join(random.sample(features, 2))
        return description

    def extract_product_data(self, item):
        """Extraire les données d'un produit"""
        try:
            # Extraire les données de base
            name_elem = item.select_one('.product__name__product') or item.select_one('.product-name')
            brand_elem = item.select_one('.product__name__brand') or item.select_one('.brand')
            price_elem = item.select_one('.price') or item.select_one('.product-price')
            
            if not name_elem or not brand_elem:
                return None
            
            # SKU from data attributes
            sku = (item.get('data-itemid') or 
                  item.get('data-sku') or 
                  f"CR{random.randint(10000, 99999)}")
            
            product_data = {
                'name': name_elem.get_text(strip=True),
                'brand': brand_elem.get_text(strip=True),
                'sku': sku,
                'base_price': self.clean_price(price_elem.get_text() if price_elem else '0'),
                'scraped_from': 'courir.com',
                'last_scraped': datetime.utcnow().isoformat()
            }
            
            # Ajouter la description générée
            product_data['description'] = self.generate_description(product_data)
            
            return product_data
            
        except Exception as e:
            logger.error(f"Erreur extraction produit: {e}")
            return None

    def scrape_page(self, url, max_products=10):
        """Scraper une page de produits"""
        logger.info(f"Scraping: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            products = []
            
            # Sélecteurs pour trouver les produits
            selectors = [
                'div.product__tile',
                'div.product-tile', 
                'article.product',
                'li.product-item'
            ]
            
            product_items = []
            for selector in selectors:
                product_items = soup.select(selector)
                if product_items:
                    logger.info(f"Trouvé {len(product_items)} produits avec {selector}")
                    break
            
            for item in product_items[:max_products]:
                product_data = self.extract_product_data(item)
                if product_data:
                    # Insérer dans Supabase
                    success = self.supabase.upsert_product(product_data)
                    if success:
                        products.append(product_data)
                    
                    time.sleep(0.5)  # Respectful delay
            
            return products
            
        except Exception as e:
            logger.error(f"Erreur scraping {url}: {e}")
            return []

    def run(self):
        """Exécuter le scraping complet"""
        logger.info("Démarrage du scraping automatique")
        
        # URLs à scraper
        urls = [
            "https://www.courir.com/fr/c/chaussures/sneakers/",
            "https://www.courir.com/fr/c/chaussures/mocassins-derbies/",
            "https://www.courir.com/fr/c/chaussures/bottines-boots/",
            "https://www.courir.com/fr/c/chaussures/claquettes-tongs-mules/",
            "https://www.courir.com/fr/c/chaussures/ballerines/",
            "https://www.courir.com/fr/c/chaussures/exclusivites/"
        ]
        
        all_products = []
        for url in urls:
            products = self.scrape_page(url, max_products=8)
            all_products.extend(products)
            time.sleep(2)  # Délai entre les URLs
        
        logger.info(f"Scraping terminé: {len(all_products)} produits traités")
        return all_products

def main():
    """Point d'entrée principal"""
    scraper = CourirScraper()
    return scraper.run()

if __name__ == "__main__":
    main()
