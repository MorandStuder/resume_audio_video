import React from 'react';
import { Container, ListGroup, Button, Spinner } from 'react-bootstrap';

const ArticleList = ({ articles, onSelectArticle, onCollectArticles, selectedArticleId, loading }) => {
  return (
    <Container className="d-flex flex-column h-100 p-0">
      <div className="p-3 bg-light border-bottom">
        <h4 className="mb-3">Articles</h4>
        <Button 
          variant="primary" 
          className="w-100" 
          onClick={onCollectArticles}
          disabled={loading}
        >
          {loading ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              <span className="ms-2">Collecte en cours...</span>
            </>
          ) : (
            'Collecter des articles'
          )}
        </Button>
      </div>
      
      <ListGroup variant="flush" className="flex-grow-1 overflow-auto">
        {articles.length === 0 ? (
          <div className="text-center p-4 text-muted">
            Aucun article disponible. Cliquez sur "Collecter des articles" pour commencer.
          </div>
        ) : (
          articles.map(article => (
            <ListGroup.Item 
              key={article.id}
              action
              active={selectedArticleId === article.id}
              onClick={() => onSelectArticle(article)}
              className="border-bottom"
            >
              <div className="d-flex justify-content-between align-items-start mb-1">
                <h6 className="mb-0 text-truncate">{article.title}</h6>
              </div>
              <div className="small text-muted d-flex justify-content-between">
                <span>{article.source}</span>
                <span>{article.date}</span>
              </div>
              {article.rating > 0 && (
                <div className="mt-1">
                  {'★'.repeat(article.rating)}{'☆'.repeat(5 - article.rating)}
                </div>
              )}
              {article.published && (
                <div className="mt-1 badge bg-success">Publié</div>
              )}
            </ListGroup.Item>
          ))
        )}
      </ListGroup>
    </Container>
  );
};

export default ArticleList;
