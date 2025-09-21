import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // Ajout de l'état loading
  const apiUrl = process.env.REACT_APP_API_URL || 'https://ecommerce-backend-production-ce4e.up.railway.app';

  useEffect(() => {
    setLoading(true); // Démarre le chargement
    axios.get(`${apiUrl}/products`)
      .then(response => setProducts(response.data))
      .catch(error => {
        console.error('Erreur:', error);
        setError('Impossible de charger les produits. Réessayez plus tard.');
      })
      .finally(() => setLoading(false)); // Arrête le chargement, même en cas d'erreur
  }, []);

  if (loading) return <p>Chargement en cours...</p>; // Affichage pendant le chargement
  if (error) return <div style={{ color: 'red' }}>{error}</div>; // Affichage en cas d'erreur

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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
