import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [cart, setCart] = useState({});
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const apiUrl = process.env.REACT_APP_API_URL || 'https://ecommerce-backend-production-ce4e.up.railway.app';

  useEffect(() => {
    axios.get(`${apiUrl}/products`)
      .then(response => {
        // Filtre les produits qui ont au moins une variante
        const filteredProducts = response.data.filter(product => 
          product.product_variants && product.product_variants.length > 0
        );
        setProducts(filteredProducts);
      })
      .catch(error => {
        console.error('Erreur:', error);
        setError('Impossible de charger les produits. Réessayez plus tard.');
      });
  }, []);

  const addToCart = async (productId) => {
    if (!token) {
      setError('Veuillez vous connecter pour ajouter au panier.');
      return;
    }
    try {
      const product = products.find(p => p.id === productId);
      console.log('Ajout au panier:', { productId, productVariants: product.product_variants });
      const variant = product.product_variants[0];
      if (!variant) {
        throw new Error('Aucune variante disponible pour ce produit.');
      }
      console.log('Ajout au panier:', { productId, variantId: variant.id, token });
      const response = await axios.get(`${apiUrl}/shopping-carts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const existingItem = response.data.find(item => item.product_variants && item.product_variants[0]?.id === variant.id);
      if (existingItem) {
        await axios.put(
          `${apiUrl}/shopping-carts/${existingItem.id}`,
          { quantity: existingItem.quantity + 1 },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } else {
        await axios.post(
          `${apiUrl}/shopping-carts`,
          { product_variant_id: variant.id, quantity: 1 },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      setCart(prev => ({ ...prev, [productId]: (prev[productId] || 0) + 1 }));
    } catch (err) {
      console.error('Erreur ajout panier:', err.response?.data || err.message);
      setError(`Erreur lors de l’ajout au panier: ${err.response?.data?.error || err.message}. Réessayez.`);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${apiUrl}/auth/login`, { email, password });
      const newToken = response.data.token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      setError(null);
    } catch (err) {
      console.error('Erreur login:', err);
      setError('Échec de la connexion. Vérifiez vos identifiants.');
    }
  };

  const handleLogout = () => {
    setToken(null);
    setCart({});
    localStorage.removeItem('token');
  };

  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div>
      <h1>E-commerce</h1>
      <div>
        {!token ? (
          <form onSubmit={handleLogin} style={{ marginBottom: '20px' }}>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              style={{ marginRight: '10px' }}
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mot de passe"
              style={{ marginRight: '10px' }}
            />
            <button type="submit">Connexion</button>
          </form>
        ) : (
          <button onClick={handleLogout} style={{ marginBottom: '20px' }}>Déconnexion</button>
        )}
      </div>
      <h2>Liste des produits</h2>
      {products.length === 0 ? (
        <p>Aucun produit disponible pour le moment.</p>
      ) : (
        <ul>
          {products.map(product => (
            <li key={product.id}>
              {product.name} - {product.base_price}€ (Stock: {product.product_variants[0]?.stock_quantity || 0})
              <button onClick={() => addToCart(product.id)} disabled={!token}>
                Ajouter au panier
              </button>
            </li>
          ))}
        </ul>
      )}
      {token && Object.keys(cart).length > 0 && (
        <div>
          <h2>Panier</h2>
          <ul>
            {Object.entries(cart).map(([id, qty]) => {
              const product = products.find(p => p.id === id);
              return <li key={id}>{product.name} x{qty}</li>;
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
