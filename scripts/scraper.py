import requests
from bs4 import BeautifulSoup
import supabase
import os
from datetime import datetime
import uuid
import time
import logging
import re
import json
import random

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CourirScraper:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.client = supabase.create_client(self.supabase_url, self.supabase_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Cache pour les marques et catégories
        self.brands_cache = {}
        self.categories_cache = {}

    def get_or_create_brand(self, brand_name):
        """Récupère ou crée une marque"""
        if not brand_name or brand_name == 'Marque inconnue':
            return None
            
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
        if not category_name:
            return None
            
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
                    'slug': category_name.lower().replace(' ', '-').replace('/', '-'),
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

    def extract_price(self, price_text):
        """Extrait le prix numérique d'un texte"""
        if not price_text:
            return 0.0
            
        try:
            # Nettoyage du texte de prix
            clean_text = price_text.replace('€', '').replace(',', '.').replace(' ', '').strip()
            # Extraction des chiffres et décimales
            price_match = re.search(r'(\d+\.?\d*)', clean_text)
            if price_match:
                return float(price_match.group(1))
            return 0.0
        except (ValueError, AttributeError):
            return 0.0

    def extract_product_data_from_listing(self, product_element):
        """Extrait les données de base d'un produit depuis la liste des produits"""
        try:
            # Extraction des données depuis l'élément HTML
            product_id = product_element.get('data-itemid', '')
            gtm_data = product_element.get('data-gtm', '{}')
            
            # Parse les données GTM
            try:
                gtm_info = json.loads(gtm_data.replace('&quot;', '"'))
            except:
                gtm_info = {}
            
            # Extraction des informations de base
            brand_name = gtm_info.get('brand', '')
            product_name = gtm_info.get('name', '')
            price = gtm_info.get('price', 0)
            sku = gtm_info.get('sku', '')
            
            # Extraction de l'URL du produit (lien cliquable de l'image)
            product_link = product_element.find('a', class_='product__link')
            product_url = product_link['href'] if product_link and product_link.has_attr('href') else ''
            if product_url and not product_url.startswith('http'):
                product_url = 'https://www.courir.com' + product_url
            
            # Extraction de l'image
            image_element = product_element.find('img', class_='frz-img')
            image_url = image_element['src'] if image_element and image_element.has_attr('src') else ''
            
            # Extraction du genre (junior, cadet, bébé)
            gender_element = product_element.find('span', class_='product__gender')
            gender = gender_element.get_text(strip=True) if gender_element else ''
            
            # Extraction des prix depuis le HTML (plus précis)
            price_element = product_element.find('span', class_='default-price')
            if price_element:
                price_text = price_element.get_text(strip=True)
                extracted_price = self.extract_price(price_text)
                if extracted_price > 0:
                    price = extracted_price
            
            # Extraction du prix promotionnel
            promo_price_element = product_element.find('span', class_='promotional-price')
            original_price = price
            if promo_price_element and 'display:none' not in promo_price_element.get('style', ''):
                promo_text = promo_price_element.get_text(strip=True)
                promo_price = self.extract_price(promo_text)
                if promo_price > 0:
                    original_price = price
                    price = promo_price
            
            return {
                'product_id': product_id,
                'brand_name': brand_name,
                'name': product_name,
                'price': price,
                'original_price': original_price if original_price != price else None,
                'sku': sku,
                'url': product_url,
                'image_url': image_url,
                'gender': gender,
                'gtm_data': gtm_info
            }
            
        except Exception as e:
            logging.error(f"Erreur extraction données listing: {e}")
            return None

    def scrape_product_details(self, product_url, product_data):
        """Scrape les détails (description et couleur) depuis la page produit après clic sur l'image"""
        try:
            response = self.session.get(product_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction de la description depuis la page détaillée
            description = ""
            description_element = soup.find('div', id='section-desc_01')
            if description_element:
                desc_text = description_element.find('p')
                if desc_text:
                    description = desc_text.get_text(strip=True)
                if not description:
                    ul_elements = description_element.find_all('li')
                    for li in ul_elements:
                        text = li.get_text(strip=True)
                        if text.startswith('Genre'):
                            description += f" {text.split('Genre')[1].strip()}."
                        elif text.startswith('Marque'):
                            description += f" Marque: {text.split('Marque')[1].strip()}."
            if not description:
                # Fallback : génère une description basique
                gender = product_data.get('gender', 'junior')
                description = f"{product_data['brand_name']} {product_data['name']} - Chaussure {gender} de qualité, idéale pour un usage quotidien. Prix: {product_data['price']}€."
            
            # Extraction de la couleur depuis la page détaillée
            color = ""
            color_section = soup.find('div', class_='product-productlinks')
            if color_section:
                color_element = color_section.find('span', class_='color-text')
                if color_element:
                    color = color_element.get_text(strip=True).lower()
            if not color:
                color = random.choice(['rouge', 'noir', 'bleu'])
            
            # Extraction des images supplémentaires
            images = []
            image_elements = soup.find_all('img', {'data-frz-src': True})
            for img in image_elements:
                if img['data-frz-src'] and img['data-frz-src'] not in images:
                    images.append(img['data-frz-src'])
            
            # Ajout des informations supplémentaires
            product_data['description'] = description
            product_data['additional_images'] = images
            product_data['color'] = color
            
            return product_data
            
        except Exception as e:
            logging.error(f"Erreur scraping détails {product_url}: {e}")
            # Fallback description et couleur en cas d'erreur scraping
            product_data['description'] = f"{product_data['brand_name']} {product_data['name']} - Chaussure junior de qualité, idéale pour un usage quotidien. Prix: {product_data['price']}€."
            product_data['additional_images'] = []
            product_data['color'] = random.choice(['rouge', 'noir', 'bleu'])
            return product_data

    def insert_product(self, product_data, category_name):
        """Insère un produit dans la base de données"""
        try:
            # Récupération des IDs
            brand_id = self.get_or_create_brand(product_data['brand_name'])
            category_id = self.get_or_create_category(category_name)
            
            # Préparation des données pour Supabase
            product_db_data = {
                'name': product_data['name'],
                'brand_id': brand_id,
                'category_id': category_id,
                'description': product_data.get('description', ''),
                'base_price': product_data['price'],
                'sku': product_data['sku'] or str(uuid.uuid4())[:12],
                'scraped_from': product_data['url'],
                'scraped_data': {
                    'original_data': product_data['gtm_data'],
                    'gender': product_data.get('gender', ''),
                    'original_price': product_data.get('original_price'),
                    'additional_images': product_data.get('additional_images', []),
                    'scraped_at': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insertion du produit
            response = self.client.from_('products').insert(product_db_data).execute()
            product_id = response.data[0]['id']
            
            # Insertion des images
            if product_data.get('image_url'):
                image_data = {
                    'product_id': product_id,
                    'image_url': product_data['image_url'],
                    'alt_text': f"{product_data['brand_name']} {product_data['name']}",
                    'is_primary': True,
                    'display_order': 0
                }
                self.client.from_('product_images').insert(image_data).execute()
            
            # Insertion des images supplémentaires
            for i, img_url in enumerate(product_data.get('additional_images', []), 1):
                if img_url and img_url != product_data.get('image_url'):
                    additional_image_data = {
                        'product_id': product_id,
                        'image_url': img_url,
                        'alt_text': f"{product_data['brand_name']} {product_data['name']} - Vue {i}",
                        'is_primary': False,
                        'display_order': i
                    }
                    self.client.from_('product_images').insert(additional_image_data).execute()
            
            # Insertion des variantes si disponible
            if 'variant' in product_data['gtm_data'] and product_data['gtm_data']['variant']:
                try:
                    size_str = product_data['gtm_data']['variant'].replace(',', '.')
                    variant_data = {
                        'product_id': product_id,
                        'size': float(size_str),
                        'color': product_data.get('color', random.choice(['rouge', 'noir', 'bleu'])),
                        'stock_quantity': random.randint(10, 50),
                        'price': product_data['price'],
                        'sku': product_data['sku'] or str(uuid.uuid4())[:12],
                        'created_at': datetime.now().isoformat()
                    }
                    self.client.from_('product_variants').insert(variant_data).execute()
                    logging.info(f"Variante ajoutée pour {product_data['name']}: taille {size_str}, couleur {variant_data['color']}")
                except ValueError:
                    logging.warning(f"Taille invalide pour {product_data['name']}: {product_data['gtm_data']['variant']}")
            
            logging.info(f"Produit inséré: {product_data['brand_name']} {product_data['name']}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur insertion produit {product_data.get('name', '')}: {e}")
            return False

    def scrape_category_page(self, category_url, category_name):
        """Scrape une page de catégorie"""
        logging.info(f"Scraping de la catégorie: {category_url}")
        
        try:
            response = self.session.get(category_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver tous les produits
            product_elements = soup.find_all('div', class_='product__tile')
            logging.info(f"Trouvé {len(product_elements)} produits avec: div.product__tile")
            
            successful_products = 0
            
            for i, product_element in enumerate(product_elements):
                try:
                    # Extraction des données de base
                    product_data = self.extract_product_data_from_listing(product_element)
                    if not product_data:
                        continue
                    
                    # Scrape les détails supplémentaires depuis la page produit
                    if product_data['url']:
                        product_data = self.scrape_product_details(product_data['url'], product_data)
                    
                    # Insertion dans la base de données
                    if self.insert_product(product_data, category_name):
                        successful_products += 1
                    
                    # Pause pour éviter le rate limiting
                    if i % 5 == 0:
                        time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Erreur produit {i}: {e}")
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
            products_count = self.scrape_category_page(category_url, category_name)
            duration = time.time() - start_time
            total_products += products_count
            logging.info(f"Catégorie {category_name} traitée en {duration:.1f}s: {products_count} produits")
            
            # Pause entre les catégories
            time.sleep(2)
        
        logging.info(f"✅ Scraping terminé: {total_products} produits traités au total")

# Exécution
if __name__ == "__main__":
    scraper = CourirScraper()
    scraper.run()
