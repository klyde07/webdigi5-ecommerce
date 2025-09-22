import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
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
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [orderStatus, setOrderStatus] = useState(null);
  
  const apiUrl = process.env.REACT_APP_API_URL || 'https://ecommerce-backend-production-ce4e.up.railway.app';

  // Charger les produits
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await axios.get(`${apiUrl}/products`);
        const filteredProducts = response.data.filter(product => 
          product.product_variants && product.product_variants.length > 0
        );
        setProducts(filteredProducts);
      } catch (error) {
        console.error('Erreur:', error);
        setError('Impossible de charger les produits. Réessayez plus tard.');
      }
    };

    fetchProducts();
  }, [apiUrl]);

  // Charger le panier si connecté
  useEffect(() => {
    const fetchCart = async () => {
      if (!token) return;
      
      try {
        const response = await axios.get(`${apiUrl}/shopping-carts`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        const newCart = {};
        response.data.forEach(item => {
          newCart[item.product_variant_id] = item.quantity;
        });
        setCart(newCart);
      } catch (err) {
        console.error('Erreur chargement panier:', err);
      }
    };

    fetchCart();
  }, [token, apiUrl]);

  const addToCart = async (productId) => {
    if (!token) {
      setError('Veuillez vous connecter pour ajouter au panier.');
      return;
    }
    
    try {
      const product = products.find(p => p.id === productId);
      if (!product || !product.product_variants[0]) return;
      
      const variant = product.product_variants[0];
      
      await axios.post(
        `${apiUrl}/shopping-carts`,
        { product_variant_id: variant.id, quantity: 1 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setCart(prev => ({ 
        ...prev, 
        [variant.id]: (prev[variant.id] || 0) + 1 
      }));
      
    } catch (err) {
      console.error('Erreur ajout panier:', err);
      setError('Erreur lors de l\'ajout au panier');
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
      setEmail('');
      setPassword('');
    } catch (err) {
      setError('Échec de la connexion. Vérifiez vos identifiants.');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    if (!signupEmail || !signupPassword || !firstName || !lastName) {
      setError('Tous les champs sont requis.');
      return;
    }
    
    try {
      await axios.post(`${apiUrl}/auth/signup`, { 
        email: signupEmail, 
        password: signupPassword, 
        first_name: firstName, 
        last_name: lastName 
      });
      setError('Inscription réussie ! Connectez-vous.');
      setSignupEmail('');
      setSignupPassword('');
      setFirstName('');
      setLastName('');
    } catch (err) {
      setError('Échec de l\'inscription. Réessayez.');
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
      const orderItems = Object.entries(cart).map(([variantId, quantity]) => ({
        product_variant_id: parseInt(variantId),
        quantity: quantity
      }));
      
      await axios.post(
        `${apiUrl}/orders`,
        { items: orderItems },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      alert('Commande passée avec succès ! (Simulation)');
      setCart({});
      setOrderStatus('confirmed');
      
    } catch (err) {
      setError('Erreur lors de la commande');
    }
  };

  // Composant principal
  return (
    <Router>
      <div className="app">
        <CookieConsent
          location="bottom"
          buttonText="Accepter"
          cookieName="ecommerceCookie"
          style={{ background: '#2B373B' }}
          buttonStyle={{ color: '#4e503b', fontSize: '13px' }}
          expires={150}
        >
          Ce site utilise des cookies pour améliorer votre expérience.
          <Link to="/confidentialite" style={{ color: '#fff', marginLeft: '5px' }}>
            En savoir plus
          </Link>
        </CookieConsent>

        <header>
          <h1>Boutique de Sneakers</h1>
          
          <div className="auth-section">
            {!token ? (
              <div className="auth-forms">
                <form onSubmit={handleLogin} className="login-form">
                  <h3>Connexion</h3>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email"
                    required
                  />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Mot de passe"
                    required
                  />
                  <button type="submit">Se connecter</button>
                </form>

                <form onSubmit={handleSignup} className="signup-form">
                  <h3>Inscription</h3>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="Prénom"
                    required
                  />
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Nom"
                    required
                  />
                  <input
                    type="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    placeholder="Email"
                    required
                  />
                  <input
                    type="password"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    placeholder="Mot de passe"
                    required
                  />
                  <button type="submit">S'inscrire</button>
                </form>
              </div>
            ) : (
              <div className="user-section">
                <button onClick={handleLogout} className="logout-btn">
                  Déconnexion
                </button>
              </div>
            )}
          </div>
        </header>

        <main>
          {error && <div className="error-message">{error}</div>}

          <section className="products-section">
            <h2>Nos Sneakers</h2>
            {products.length === 0 ? (
              <p>Chargement des produits...</p>
            ) : (
              <div className="products-grid">
                {products.map(product => (
                  <div key={product.id} className="product-card">
                    <h3>{product.name}</h3>
                    <p>Prix: {product.base_price}€</p>
                    <p>Stock: {product.product_variants[0]?.stock_quantity || 0}</p>
                    <button 
                      onClick={() => addToCart(product.id)} 
                      disabled={!token || (product.product_variants[0]?.stock_quantity || 0) === 0}
                    >
                      {!token ? 'Connectez-vous' : 'Ajouter au panier'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {token && Object.keys(cart).length > 0 && (
            <section className="cart-section">
              <h2>Votre Panier</h2>
              <div className="cart-items">
                {Object.entries(cart).map(([variantId, quantity]) => {
                  const product = products.find(p => 
                    p.product_variants.some(v => v.id === parseInt(variantId))
                  );
                  const variant = product?.product_variants.find(v => v.id === parseInt(variantId));
                  
                  return product && variant ? (
                    <div key={variantId} className="cart-item">
                      <span>{product.name} (Taille: {variant.size}) x {quantity}</span>
                    </div>
                  ) : null;
                })}
              </div>
              <button onClick={handleCheckout} className="checkout-btn">
                Passer commande
              </button>
              {orderStatus && <p>Statut: {orderStatus}</p>}
            </section>
          )}
        </main>

        <Routes>
          <Route path="/confidentialite" element={<Confidentialite />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
