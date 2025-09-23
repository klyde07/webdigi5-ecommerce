import React, { useState } from 'react';
import axios from 'axios';

function AdminLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const apiUrl = process.env.REACT_APP_API_URL || 'https://ecommerce-backend-production-ce4e.up.railway.app';

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${apiUrl}/auth/login`, { email, password });
      const newToken = response.data.token;
      localStorage.setItem('token', newToken);
      window.location.href = '/'; // Redirige vers page principale
    } catch (err) {
      console.error('Erreur login admin:', err);
      setError('Échec de la connexion. Vérifiez vos identifiants.');
    }
  };

  return (
    <div>
      <h1>Connexion Admin/Vendeur</h1>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleAdminLogin}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe" />
        <button type="submit">Connexion</button>
      </form>
      <p>Utilisez vos identifiants admin ou vendeur fournis.</p>
    </div>
  );
}

export default AdminLogin;
