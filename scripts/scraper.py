import requests
from bs4 import BeautifulSoup
import supabase
import os
from datetime import datetime
import uuid
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CourirScraper:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.client = supabase.create_client(self.supabase_url, self.supabase_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cache pour les marques et catégories
        self.brands_cache = {}
        self.categories_cache = {}

    def get_or_create_brand(self, brand_name):
        """Récupère ou crée une marque"""
        if brand_name in self.brands_cache:
            return self.brands_cache[brand_name]
        
        try:
            # Vérifie si la marque existe déjà
            response = self.client.from_('brands').select('id').eq('name', brand_name).execute()
            
            if response.data:
                brand_id = response.data[0]['id']
            else:
                # Crée la marque
                new_brand = {
                    'name': brand_name,
                    'created_at': datetime.now().isoformat()
                }
                response = self.client.from_('brands').insert(new_brand).execute()
                brand_id = response.data[0]['id']
            
            self.brands_cache[brand_name] = brand_id
            return brand_id
            
        except Exception as e:
            logging.error(f"Erreur avec la marque {brand_name}: {e}")
            return None

    def get_or_create_category(self, category_name, parent_id=None):
        """Récupère ou crée une catégorie"""
        cache_key = f"{category_name}_{parent_id}"
        if cache_key in self.categories_cache:
            return self.categories_cache[cache_key]
        
        try:
            # Vérifie si la catégorie existe déjà
            query = self.client.from_('categories').select('id').eq('name', category_name)
            if parent_id:
                query = query.eq('parent_id', parent_id)
            else:
                query = query.is_('parent_id', 'null')
            
            response = query.execute()
            
            if response.data:
                category_id = response.data[0]['id']
            else:
                # Crée la catégorie
                new_category = {
                    'name': category_name,
                    'slug': category_name.lower().replace(' ', '-'),
                    'parent_id': parent_id,
                    'created_at': datetime.now().isoformat()
                }
                response = self.client.from_('categories').insert(new_category).execute()
                category_id = response.data[0]['id']
            
            self.categories_cache[cache_key] = category_id
            return category_id
            
        except Exception as e:
            logging.error(f"Erreur avec la catégorie {category_name}: {e}")
            return None

    def scrape_product(self, product_url, category_name):
        """Scrape les détails d'un produit"""
        try:
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction des données du produit
            # (Adaptez ces sélecteurs selon le site Courir)
            name = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'Nom inconnu'
            brand_name = soup.find('meta', {'property': 'brand'}) or 'Marque inconnue'
            price_text = soup.find('span', {'class': 'price'}).get_text(strip=True) if soup.find('span', {'class': 'price'}) else '0'
            description = soup.find('div', {'class': 'description'}).get_text(strip=True) if soup.find('div', {'class': 'description'}) else ''
            
            # Nettoyage du prix
            price = float(''.join(filter(str.isdigit, price_text))) / 100 if price_text else 0
            
            # Récupération des IDs
            brand_id = self.get_or_create_brand(brand_name)
            category_id = self.get_or_create_category(category_name)
            
            product_data = {
                'name': name,
                'brand_id': brand_id,
                'category_id': category_id,
                'description': description,
                'base_price': price,
                'sku': str(uuid.uuid4())[:8],  # SKU temporaire
                'scraped_from': product_url,
                'scraped_data': {
                    'original_url': product_url,
                    'scraped_at': datetime.now().isoformat(),
                    'raw_price': price_text
                },
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            return product_data
            
        except Exception as e:
            logging.error(f"Erreur scraping produit {product_url}: {e}")
            return None

    def scrape_category(self, category_url, category_name):
        """Scrape tous les produits d'une catégorie"""
        logging.info(f"Scraping de la catégorie: {category_url}")
        
        try:
            response = self.session.get(category_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver tous les produits (adaptez le sélecteur)
            products = soup.find_all('div', class_='product__tile')
            logging.info(f"Trouvé {len(products)} produits avec: div.product__tile")
            
            successful_products = 0
            
            for product in products:
                try:
                    # Extraction du lien produit (adaptez le sélecteur)
                    product_link = product.find('a', href=True)
                    if not product_link:
                        continue
                    
                    product_url = product_link['href']
                    if not product_url.startswith('http'):
                        product_url = 'https://www.courir.com' + product_url
                    
                    # Scrape les détails du produit
                    product_data = self.scrape_product(product_url, category_name)
                    if not product_data:
                        continue
                    
                    # Insertion dans Supabase
                    response = self.client.from_('products').insert(product_data).execute()
                    successful_products += 1
                    logging.info(f"Produit inséré: {product_data['name']}")
                    
                    # Pause pour éviter le rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Erreur produit: {e}")
                    continue
            
            return successful_products
            
        except Exception as e:
            logging.error(f"Erreur catégorie {category_url}: {e}")
            return 0

    def run(self):
        """Lance le scraping complet"""
        logging.info("🚀 Démarrage du scraping automatique Courir.com")
        
        categories = [
            ('https://www.courir.com/fr/c/chaussures/sneakers/', 'Sneakers'),
            ('https://www.courir.com/fr/c/chaussures/mocassins-derbies/', 'Mocassins & Derbies'),
            ('https://www.courir.com/fr/c/chaussures/bottines-boots/', 'Bottines & Boots'),
            ('https://www.courir.com/fr/c/chaussures/claquettes-tongs-mules/', 'Claquettes & Tongs'),
            ('https://www.courir.com/fr/c/chaussures/ballerines/', 'Ballerines'),
            ('https://www.courir.com/fr/c/chaussures/exclusivites/', 'Exclusivités')
        ]
        
        total_products = 0
        
        for category_url, category_name in categories:
            start_time = time.time()
            products_count = self.scrape_category(category_url, category_name)
            duration = time.time() - start_time
            total_products += products_count
            logging.info(f"Catégorie traitée en {duration:.1f}s: {products_count} produits")
        
        logging.info(f"✅ Scraping terminé: {total_products} produits traités")

# Exécution
if __name__ == "__main__":
    scraper = CourirScraper()
    scraper.run()
