import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [cart, setCart] = useState({});
  const [token, setToken] = useState(localStorage.getItem('token') || null); // Stocke le token
  const apiUrl = process.env.REACT_APP_API_URL || 'https://ecommerce-backend-production-ce4e.up.railway.app';

  useEffect(() => {
    axios.get(`${apiUrl}/products`)
      .then(response => setProducts(response.data))
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
      const variant = product.product_variants[0]; // Prend la première variante pour simplifier
      await axios.post(
        `${apiUrl}/shopping-carts`,
        { product_variant_id: variant.id, quantity: 1 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCart(prev => ({ ...prev, [productId]: (prev[productId] || 0) + 1 }));
    } catch (err) {
      console.error('Erreur ajout panier:', err);
      setError('Erreur lors de l’ajout au panier. Réessayez.');
    }
  };

  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div>
      <h1>Liste des produits</h1>
      {products.length === 0 ? (
        <p>Aucun produit disponible pour le moment.</p>
      ) : (
        <ul>
          {products.map(product => (
            <li key={product.id}>
              {product.name} - {product.base_price}€ (Stock: {product.product_variants[0]?.stock_quantity || 0})
              <button onClick={() => addToCart(product.id)}>Ajouter au panier</button>
            </li>
          ))}
        </ul>
      )}
      {Object.keys(cart).length > 0 && (
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
