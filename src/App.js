import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    axios.get('https://ecommerce-backend-production-ce4e.up.railway.app/products')
      .then(response => setProducts(response.data))
      .catch(error => console.error('Erreur:', error));
  }, []);

  return (
    <div>
      <h1>Liste des produits</h1>
      <ul>
        {products.map(product => (
          <li key={product.id}>
            {product.name} - {product.base_price}€ (Stock: {product.product_variants[0]?.stock_quantity || 0})
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
