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
from typing import List, Dict, Any, Optional
from supabase import create_client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CourirScraper:
    def __init__(self):
        self.supabase = self._init_supabase()
        self.session = self._create_session()
        
    def _init_supabase(self):
        """Initialiser la connexion Supabase"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE')
            
            if not supabase_url or not supabase_key:
                logger.warning("Variables Supabase non configurées - mode simulation")
                return None
                
            return create_client(supabase_url, supabase_key)
        except Exception as e:
            logger.error(f"Erreur connexion Supabase: {e}")
            return None
    
    def _create_session(self):
        """Créer une session requests"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        return session

    def clean_price(self, price_text):
        """Nettoyer et convertir les prix en float"""
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

    def generate_product_description(self, product_data: Dict[str, Any]) -> str:
        """Générer une description automatique"""
        name = product_data.get('name', 'Produit')
        brand = product_data.get('brand', 'Marque inconnue')
        price = product_data.get('base_price', 0)
        category = product_data.get('category', '')
        
        description = f"{brand} {name}. Chaussure de qualité supérieure."
        
        if category:
            category_clean = category.replace('HOMME-', '').replace('CHAUSSURES-', '').lower()
            description += f" Catégorie: {category_clean.capitalize()}."
        
        if price > 0:
            description += f" Prix: {price}€."
        
        features = [
            "Semelle confortable pour un usage quotidien.",
            "Design moderne et tendance.",
            "Matériaux de haute qualité.",
            "Parfait pour le sport et le casual.",
            "Style urbain et contemporain.",
            "Confort optimal toute la journée."
        ]
        
        description += " " + " ".join(random.sample(features, 2))
        return description

    def extract_gtm_data(self, item) -> Dict[str, Any]:
        """Extraire les données GTM"""
        gtm_data = {}
        if item.get('data-gtm'):
            try:
                gtm_data = json.loads(item['data-gtm'].replace('&quot;', '"'))
            except:
                try:
                    gtm_str = item['data-gtm'].replace('&quot;', '"')
                    matches = re.findall(r'(\w+):"([^"]+)"', gtm_str)
                    gtm_data = {k: v for k, v in matches}
                except:
                    pass
        
        data_attributes = {
            'data-itemid': 'item_id',
            'data-product-category': 'category',
            'data-product-retailer': 'retailer'
        }
        
        for attr, key in data_attributes.items():
            if item.get(attr):
                gtm_data[key] = item[attr]
        
        return gtm_data

    def extract_product_data(self, item) -> Optional[Dict[str, Any]]:
        """Extraire les données d'un produit"""
        try:
            gtm_data = self.extract_gtm_data(item)
            
            # Nom et marque
            name_elem = item.select_one('.product__name__product') or item.select_one('[data-product-name]')
            brand_elem = item.select_one('.product__name__brand') or item.select_one('[data-brand]')
            
            if not name_elem or not brand_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            brand = brand_elem.get_text(strip=True)
            
            # Prix
            price_elem = item.select_one('.price') or item.select_one('[data-price]')
            price = self.clean_price(price_elem.get_text() if price_elem else '0')
            
            # SKU
            sku = gtm_data.get('sku') or item.get('data-itemid') or hashlib.md5(f"{brand}{name}".encode()).hexdigest()[:8]
            
            # Catégorie
            category = gtm_data.get('category', '')
            
            # Description
            description = self.generate_product_description({
                'name': name, 'brand': brand, 'base_price': price, 'category': category
            })
            
            product_data = {
                "name": name,
                "brand": brand,
                "sku": sku.upper(),
                "base_price": price or 0.0,
                "description": description,
                "category": category,
                "scraped_from": "courir.com",
                "scraped_data": gtm_data,
                "last_scraped": datetime.utcnow().isoformat()
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"Erreur extraction produit: {e}")
            return None

    def check_existing_product(self, sku: str) -> bool:
        """Vérifier si le produit existe déjà"""
        if not self.supabase:
            return False
            
        try:
            response = self.supabase.table('products')\
                .select('sku')\
                .eq('sku', sku)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Erreur vérification produit {sku}: {e}")
            return False

    def upsert_product(self, product_data: Dict[str, Any]) -> bool:
        """Insérer ou mettre à jour un produit"""
        try:
            sku = product_data['sku']
            
            if self.supabase:
                # Vérifier l'existence
                exists = self.check_existing_product(sku)
                
                db_data = {
                    'name': product_data['name'],
                    'brand': product_data['brand'],
                    'sku': sku,
                    'base_price': product_data['base_price'],
                    'description': product_data['description'],
                    'category': product_data['category'],
                    'scraped_from': product_data['scraped_from'],
                    'scraped_data': json.dumps(product_data['scraped_data']),
                    'last_scraped': product_data['last_scraped']
                }
                
                if exists:
                    # Mise à jour
                    self.supabase.table('products')\
                        .update(db_data)\
                        .eq('sku', sku)\
                        .execute()
                    logger.info(f"Produit mis à jour: {sku}")
                else:
                    # Insertion
                    self.supabase.table('products').insert(db_data).execute()
                    logger.info(f"Nouveau produit inséré: {sku}")
                
                return True
            else:
                # Mode simulation
                action = "MISE À JOUR" if random.random() > 0.7 else "INSERTION"
                logger.info(f"SIMULATION {action}: {product_data['name']} ({sku})")
                return True
                
        except Exception as e:
            logger.error(f"Erreur upsert produit {product_data.get('sku')}: {e}")
            return False

    def scrape_category(self, url: str, max_products: int = 15) -> List[Dict[str, Any]]:
        """Scraper une catégorie spécifique"""
        logger.info(f"Scraping de la catégorie: {url}")
        
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
                'li.product-item',
                '[data-gtm]'
            ]
            
            product_items = []
            for selector in selectors:
                product_items = soup.select(selector)
                if product_items:
                    logger.info(f"Trouvé {len(product_items)} produits avec: {selector}")
                    break
            
            if not product_items:
                logger.warning(f"Aucun produit trouvé sur: {url}")
                return []
            
            for i, item in enumerate(product_items[:max_products]):
                product_data = self.extract_product_data(item)
                if product_data:
                    success = self.upsert_product(product_data)
                    if success:
                        products.append(product_data)
                    
                    # Délai respectueux entre les produits
                    time.sleep(random.uniform(0.5, 1.5))
            
            return products
            
        except Exception as e:
            logger.error(f"Erreur scraping {url}: {e}")
            return []

    def run(self):
        """Exécuter le scraping complet"""
        logger.info("🚀 Démarrage du scraping automatique Courir.com")
        
        # URLs des catégories à scraper
        categories = [
            "https://www.courir.com/fr/c/chaussures/sneakers/",
            "https://www.courir.com/fr/c/chaussures/mocassins-derbies/",
            "https://www.courir.com/fr/c/chaussures/bottines-boots/",
            "https://www.courir.com/fr/c/chaussures/claquettes-tongs-mules/",
            "https://www.courir.com/fr/c/chaussures/ballerines/",
            "https://www.courir.com/fr/c/chaussures/exclusivites/"
        ]
        
        all_products = []
        total_start_time = time.time()
        
        for category_url in categories:
            try:
                category_start_time = time.time()
                products = self.scrape_category(category_url, max_products=12)
                all_products.extend(products)
                
                category_time = time.time() - category_start_time
                logger.info(f"Catégorie traitée en {category_time:.1f}s: {len(products)} produits")
                
                # Délai entre les catégories
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Erreur avec la catégorie {category_url}: {e}")
                continue
        
        total_time = time.time() - total_start_time
        logger.info(f"✅ Scraping terminé en {total_time:.1f}s")
        logger.info(f"📊 Total: {len(all_products)} produits traités")
        
        return all_products

def main():
    """Point d'entrée principal"""
    scraper = CourirScraper()
    return scraper.run()

if __name__ == "__main__":
    main()
