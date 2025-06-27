import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import ArticleList from './ArticleList';
import ArticleReader from './ArticleReader';
import SummaryEditor from './SummaryEditor';

const AppLayout = ({ 
  articles, 
  selectedArticle, 
  summary, 
  loading, 
  error,
  onSelectArticle, 
  onCollectArticles, 
  onRateArticle, 
  onGenerateSummary, 
  onSummaryChange,
  onPublishToLinkedIn
}) => {
  return (
    <Container fluid className="vh-100">
      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          {error}
          <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      )}
      <Row className="h-100">
        {/* Colonne de gauche - Liste des articles */}
        <Col md={3} className="border-end p-0 h-100 overflow-auto">
          <ArticleList 
            articles={articles} 
            onSelectArticle={onSelectArticle}
            onCollectArticles={onCollectArticles}
            selectedArticleId={selectedArticle?.id}
            loading={loading}
          />
        </Col>
        
        {/* Colonne centrale - Lecteur d'article */}
        <Col md={5} className="border-end p-0 h-100 overflow-auto">
          <ArticleReader 
            article={selectedArticle} 
            onRateArticle={onRateArticle}
          />
        </Col>
        
        {/* Colonne de droite - Résumé et édition */}
        <Col md={4} className="p-0 h-100 overflow-auto">
          <SummaryEditor 
            article={selectedArticle}
            summary={summary}
            onGenerateSummary={onGenerateSummary}
            onSummaryChange={onSummaryChange}
            onPublishToLinkedIn={onPublishToLinkedIn}
            loading={loading}
          />
        </Col>
      </Row>
    </Container>
  );
};

export default AppLayout;
