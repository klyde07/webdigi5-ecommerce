import React, { useEffect, useState } from 'react';
import axios from 'axios';
import CookieConsent from 'react-cookie-consent';
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

  useEffect(() => {
    axios.get(`${apiUrl}/products`)
      .then(response => {
        setProducts(response.data);
      })
      .catch(error => {
        console.error('Erreur:', error);
        setError('Impossible de charger les produits.');
      });

    if (token) {
      axios.get(`${apiUrl}/shopping-carts`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(response => {
          const newCart = {};
          response.data.forEach(item => newCart[item.product_id] = item.quantity);
          setCart(newCart);
        })
        .catch(err => console.error('Erreur chargement panier:', err));
    }
  }, [token]);

  const addToCart = async (productId) => {
    if (!token) {
      setError('Veuillez vous connecter pour ajouter au panier.');
      return;
    }
    try {
      await axios.post(
        `${apiUrl}/shopping-carts`,
        { product_id: productId, quantity: 1 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCart(prev => ({ ...prev, [productId]: (prev[productId] || 0) + 1 }));
    } catch (err) {
      console.error('Erreur ajout panier:', err);
      setError('Erreur lors de l’ajout au panier.');
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
      setError('Échec de la connexion.');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    if (!signupEmail || !signupPassword || !firstName || !lastName) {
      setError('Tous les champs sont requis.');
      return;
    }
    try {
      const response = await axios.post(`${apiUrl}/auth/signup`, { 
        email: signupEmail, 
        password: signupPassword, 
        first_name: firstName, 
        last_name: lastName 
      });
      const newToken = response.data.token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      setError('Inscription réussie.');
    } catch (err) {
      console.error('Erreur signup:', err);
      setError('Échec de l’inscription.');
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
      const items = Object.keys(cart).map(productId => ({ product_id: productId, quantity: cart[productId] }));
      await axios.post(
        `${apiUrl}/orders`,
        { items },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setOrderStatus('Commande passée');
      setCart({});
    } catch (err) {
      console.error('Erreur checkout:', err);
      setError('Erreur lors de la commande.');
    }
  };

  if (error) return <div className="error">{error}</div>;

  return (
    <div>
      <CookieConsent
        location="bottom"
        buttonText="Accepter"
        cookieName="myAwesomeCookie"
        style={{ background: '#2B373B' }}
        buttonStyle={{ color: '#4e503b', fontSize: '13px' }}
        expires={150}
      >
        Cookies info
      </CookieConsent>
      <h1>E-commerce</h1>
      {!token ? (
        <>
          <form onSubmit={handleLogin}>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe" />
            <button type="submit">Connexion</button>
          </form>
          <form onSubmit={handleSignup}>
            <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Prénom" />
            <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Nom" />
            <input type="email" value={signupEmail} onChange={(e) => setSignupEmail(e.target.value)} placeholder="Email" />
            <input type="password" value={signupPassword} onChange={(e) => setSignupPassword(e.target.value)} placeholder="Mot de passe" />
            <button type="submit">Inscription</button>
          </form>
        </>
      ) : (
        <button onClick={handleLogout}>Déconnexion</button>
      )}
      <h2>Produits</h2>
      {products.length === 0 ? (
        <p>Chargement...</p>
      ) : (
        <ul>
          {products.map(product => (
            <li key={product.id}>
              {product.name} - {product.base_price}€
              <button onClick={() => addToCart(product.id)} disabled={!token}>Ajouter</button>
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
          {orderStatus && <p>{orderStatus}</p>}
        </div>
      )}
    </div>
  );
}

export default App;
