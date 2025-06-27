import React, { useEffect } from 'react';
import AppLayout from './components/AppLayout';
import api from './services/api';
import './App.css';

function App() {
  // Mise à jour des composants pour utiliser l'API
  const [articles, setArticles] = React.useState([]);
  const [selectedArticle, setSelectedArticle] = React.useState(null);
  const [summary, setSummary] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  // Charger les articles au démarrage
  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const data = await api.getArticles();
        setArticles(data);
      } catch (err) {
        console.error('Erreur lors du chargement des articles:', err);
        setError('Erreur lors du chargement des articles');
      }
    };

    fetchArticles();
  }, []);

  // Fonction pour collecter des articles
  const handleCollectArticles = async () => {
    setLoading(true);
    setError(null);
    try {
      const newArticles = await api.collectArticles();
      setArticles([...articles, ...newArticles]);
    } catch (err) {
      console.error('Erreur lors de la collecte des articles:', err);
      setError('Erreur lors de la collecte des articles');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour sélectionner un article
  const handleSelectArticle = (article) => {
    setSelectedArticle(article);
    setSummary(article.summary || '');
  };

  // Fonction pour noter un article
  const handleRateArticle = async (articleId, rating) => {
    try {
      const updatedArticle = await api.updateArticleRating(articleId, rating);
      setArticles(articles.map(article => 
        article.id === articleId ? updatedArticle : article
      ));
      if (selectedArticle && selectedArticle.id === articleId) {
        setSelectedArticle(updatedArticle);
      }
    } catch (err) {
      console.error('Erreur lors de la notation de l\'article:', err);
      setError('Erreur lors de la notation de l\'article');
    }
  };

  // Fonction pour générer un résumé
  const handleGenerateSummary = async () => {
    if (!selectedArticle) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.generateSummary(selectedArticle.id);
      setSummary(response.summary);
      // Mettre à jour l'article dans la liste
      const updatedArticle = { ...selectedArticle, summary: response.summary };
      setSelectedArticle(updatedArticle);
      setArticles(articles.map(article => 
        article.id === selectedArticle.id ? updatedArticle : article
      ));
    } catch (err) {
      console.error('Erreur lors de la génération du résumé:', err);
      setError('Erreur lors de la génération du résumé');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour publier sur LinkedIn
  const handlePublishToLinkedIn = async () => {
    if (!selectedArticle || !summary) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.publishToLinkedIn(selectedArticle.id, summary);
      if (response.success) {
        // Mettre à jour l'article dans la liste
        const updatedArticle = { 
          ...selectedArticle, 
          published: true,
          published_date: response.published_date,
          summary: summary
        };
        setSelectedArticle(updatedArticle);
        setArticles(articles.map(article => 
          article.id === selectedArticle.id ? updatedArticle : article
        ));
        alert(`Publication réussie: ${response.message}`);
      } else {
        setError(`Échec de la publication: ${response.message}`);
      }
    } catch (err) {
      console.error('Erreur lors de la publication sur LinkedIn:', err);
      setError('Erreur lors de la publication sur LinkedIn');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header bg-dark text-white p-3">
        <h1>Eleven Strategy - Veille LinkedIn</h1>
      </header>
      <main>
        <AppLayout 
          articles={articles}
          selectedArticle={selectedArticle}
          summary={summary}
          loading={loading}
          error={error}
          onSelectArticle={handleSelectArticle}
          onCollectArticles={handleCollectArticles}
          onRateArticle={handleRateArticle}
          onGenerateSummary={handleGenerateSummary}
          onSummaryChange={setSummary}
          onPublishToLinkedIn={handlePublishToLinkedIn}
        />
      </main>
    </div>
  );
}

export default App;
