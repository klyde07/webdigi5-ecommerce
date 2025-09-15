# WebDigi5 - E-commerce Bootcamp Project

## 🎯 Objectifs
Projet e-commerce complet réalisé dans le cadre du Bootcamp Web Digi5 (2025-2026).  
L’application permet de gérer un catalogue de produits (scrapés depuis des sites), un panier, des commandes, et une interface d’administration sécurisée.

---

## 🛠️ Stack Technique
- **Frontend** : React / Next.js (déploiement Vercel)
- **Backend** : Node.js + Express (hébergement Railway / Render)
- **Base de données** : PostgreSQL (Supabase)
- **Scraping** : Python (BeautifulSoup, exécuté sur Google Colab ou GitHub Actions)
- **Sécurité** : JWT, bcrypt, validations backend, RGPD conforme

---

## 📂 Structure du projet
db/
├── schema.sql # schéma complet de la base de données
├── seed.sql # données de test à insérer
frontend/ # application React / Next.js
backend/ # API Node.js / Express


---

## 🗄️ Base de données
1. Créer un projet PostgreSQL sur [Supabase](https://supabase.com/).  
2. Exécuter le script [`db/schema.sql`](db/schema.sql) dans le SQL Editor pour créer les tables.  
3. Exécuter ensuite [`db/seed.sql`](db/seed.sql) pour insérer des données de test.  
4. Vérifier dans **Table Editor** que les données sont présentes.

---

## 🚀 Lancer le projet (plus tard)
- Frontend : déployer sur Vercel (`npm run dev` en local, `git push` pour déploiement).  
- Backend : déployer sur Railway ou Render.  
- Configurer les variables d’environnement :
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE`
  - `SUPABASE_ANON_KEY`

---

## 👥 Auteurs
- Étudiant Bootcamp Web Digi5
