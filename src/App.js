import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import CookieConsent from 'react-cookie-consent';
import Confidentialite from './Confidentialite';
import './styles.css';

function App() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [cart, setCart] = useState({});
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orderStatus, setOrderStatus] = useState(null); // Nouvel état pour le statut
  const apiUrl = process.env.REACT_APP_API_URL || 'https://ecommerce-backend-production-ce4e.up.railway.app';

  useEffect(() => {
    axios.get(`${apiUrl}/products`)
      .then(response => {
        const filteredProducts = response.data.filter(product => 
          product.product_variants && product.product_variants.length > 0
        );
        setProducts(filteredProducts);
      })
      .catch(error => {
        console.error('Erreur:', error);
        setError('Impossible de charger les produits. Réessayez plus tard.');
      });

    if (token) {
      axios.get(`${apiUrl}/shopping-carts`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(response => {
        const newCart = {};
        response.data.forEach(item => {
          const product = products.find(p => p.product_variants.some(v => v.id === item.product_variant_id));
          if (product) newCart[product.id] = item.quantity;
        });
        setCart(newCart);
      })
      .catch(err => console.error('Erreur chargement panier:', err));
    }
  }, [token, products]);

  const addToCart = async (productId) => {
    if (!token) {
      setError('Veuillez vous connecter pour ajouter au panier.');
      return;
    }
    try {
      const product = products.find(p => p.id === productId);
      const variant = product.product_variants[0];
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

  const handleCheckout = async () => {
    if (!token) {
      setError('Veuillez vous connecter pour passer commande.');
      return;
    }
    try {
      const orderItems = Object.keys(cart).map(productId => {
        const product = products.find(p => p.id === productId);
        const variant = product.product_variants[0];
        return { product_variant_id: variant.id, quantity: cart[productId] };
      });
      await axios.post(
        `${apiUrl}/orders`,
        { items: orderItems },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Vérifie le statut de la dernière commande
      const response = await axios.get(`${apiUrl}/orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const latestOrder = response.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];
      setOrderStatus(latestOrder?.status || 'Inconnu');
      alert('Commande passée avec succès ! (Simulation)');
      setCart({}); // Vide le panier
    } catch (err) {
      console.error('Erreur checkout:', err.response?.data || err.message);
      setError(`Erreur lors de la commande: ${err.response?.data?.error || err.message}. Réessayez.`);
    }
  };

  if (error) return <div className="error">{error}</div>;

  return (
    <Router>
      <div>
        <CookieConsent
          location="bottom"
          buttonText="Accepter"
          cookieName="myAwesomeCookie"
          style={{ background: '#2B373B' }}
          buttonStyle={{ color: '#4e503b', fontSize: '13px' }}
          expires={150}
        >
          Ce site utilise des cookies pour améliorer votre expérience.{' '}
          <Link to="/confidentialite" style={{ color: '#fff' }}>En savoir plus</Link>
        </CookieConsent>
        <h1>E-commerce</h1>
        <div>
          {!token ? (
            <form onSubmit={handleLogin}>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mot de passe"
              />
              <button type="submit">Connexion</button>
            </form>
          ) : (
            <button onClick={handleLogout}>Déconnexion</button>
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
            <button onClick={handleCheckout}>Passer commande</button>
            {orderStatus && <p>Statut de votre dernière commande : {orderStatus}</p>}
          </div>
        )}
      </div>
      <Routes>
        <Route path="/confidentialite" element={<Confidentialite />} />
      </Routes>
    </Router>
  );
}

export default App;
