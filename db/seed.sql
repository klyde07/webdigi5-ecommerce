
-- db/seed.sql : données minimales de test
INSERT INTO brands (name, logo_url) VALUES
('BrandTest', 'https://example.com/logo.png');

INSERT INTO categories (name, slug) VALUES
('Sneakers', 'sneakers');

-- Produit de test (CORRIGÉ)
INSERT INTO products (name, brand_id, category_id, description, base_price, sku, scraped_from, scraped_data)
VALUES (
  'Sneaker Test Model',
  (SELECT id FROM brands LIMIT 1),
  (SELECT id FROM categories LIMIT 1),
  'Description test pour la sneaker',
  119.99,
  'SNK-TEST-001',
  'courir.com',
  jsonb_build_object('source_id', '12345', 'sizes', '["40", "41", "42"]')
);

-- Variante
INSERT INTO product_variants (product_id, size, color, stock_quantity, price, sku)
VALUES (
  (SELECT id FROM products WHERE sku='SNK-TEST-001'),
  42.0,
  'White',
  10,
  119.99,
  'SNK-TEST-001-42-W'
);

-- Image
INSERT INTO product_images (product_id, image_url, alt_text, is_primary, display_order)
VALUES (
  (SELECT id FROM products WHERE sku='SNK-TEST-001'),
  'https://example.com/sneaker1.jpg',
  'Sneaker test image',
  true,
  0
);
