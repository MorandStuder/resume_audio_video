import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = {
  // Récupérer tous les articles
  getArticles: async () => {
    try {
      const response = await axios.get(`${API_URL}/articles`);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des articles:', error);
      throw error;
    }
  },

  // Récupérer un article spécifique
  getArticle: async (id) => {
    try {
      const response = await axios.get(`${API_URL}/articles/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la récupération de l'article ${id}:`, error);
      throw error;
    }
  },

  // Collecter des articles
  collectArticles: async () => {
    try {
      const response = await axios.post(`${API_URL}/collect`);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la collecte des articles:', error);
      throw error;
    }
  },

  // Mettre à jour la notation d'un article
  updateArticleRating: async (id, rating) => {
    try {
      const response = await axios.put(`${API_URL}/articles/${id}`, { rating });
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la mise à jour de la notation de l'article ${id}:`, error);
      throw error;
    }
  },

  // Générer un résumé pour un article
  generateSummary: async (articleId) => {
    try {
      const response = await axios.post(`${API_URL}/summarize`, { article_id: articleId });
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la génération du résumé pour l'article ${articleId}:`, error);
      throw error;
    }
  },

  // Publier un article sur LinkedIn
  publishToLinkedIn: async (articleId, summary) => {
    try {
      const response = await axios.post(`${API_URL}/publish`, { 
        article_id: articleId, 
        summary 
      });
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la publication sur LinkedIn pour l'article ${articleId}:`, error);
      throw error;
    }
  }
};

export default api;
