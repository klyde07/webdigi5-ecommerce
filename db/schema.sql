-- db/schema.sql
-- Tables principales (PostgreSQL, UUID)
CREATE TABLE brands (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name varchar(100) NOT NULL,
  logo_url text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE categories (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name varchar(100) NOT NULL,
  slug varchar(100) UNIQUE,
  parent_id uuid REFERENCES categories(id),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE products (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name varchar(255) NOT NULL,
  brand_id uuid REFERENCES brands(id),
  category_id uuid REFERENCES categories(id),
  description text,
  base_price numeric(10,2),
  sku varchar(50) UNIQUE,
  is_active boolean DEFAULT true,
  scraped_from text,
  scraped_data jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX products_name_trgm_idx ON products USING gin (name gin_trgm_ops);
CREATE INDEX products_scraped_data_gin ON products USING gin (scraped_data);

CREATE TABLE product_variants (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  product_id uuid REFERENCES products(id) ON DELETE CASCADE,
  size numeric(4,1),
  color varchar(50),
  stock_quantity integer DEFAULT 0,
  price numeric(10,2),
  sku varchar(50) UNIQUE,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE product_images (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  product_id uuid REFERENCES products(id) ON DELETE CASCADE,
  image_url varchar(500) NOT NULL,
  alt_text varchar(255),
  is_primary boolean DEFAULT false,
  display_order integer DEFAULT 0
);

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email varchar(255) UNIQUE NOT NULL,
  password_hash varchar(255) NOT NULL,
  first_name varchar(100),
  last_name varchar(100),
  role varchar(50) DEFAULT 'customer',
  is_active boolean DEFAULT true,
  email_verified boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE user_sessions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  token_hash varchar(255),
  expires_at timestamptz,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE permissions (
  id serial PRIMARY KEY,
  name varchar(100) UNIQUE,
  description text
);

CREATE TABLE role_permissions (
  role varchar(50),
  permission_id integer REFERENCES permissions(id),
  PRIMARY KEY (role, permission_id)
);

CREATE TABLE orders (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id),
  order_number varchar(50) UNIQUE,
  status varchar(30) DEFAULT 'pending',
  total_amount numeric(10,2),
  shipping_address text,
  billing_address text,
  payment_method varchar(50),
  payment_status varchar(30) DEFAULT 'pending',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE order_items (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  order_id uuid REFERENCES orders(id) ON DELETE CASCADE,
  product_variant_id uuid REFERENCES product_variants(id),
  quantity integer NOT NULL,
  unit_price numeric(10,2),
  total_price numeric(10,2),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE shopping_carts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id),
  product_variant_id uuid REFERENCES product_variants(id),
  quantity integer NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id, product_variant_id)
);

