import React from 'react';
import { Container, Card, Button, Form } from 'react-bootstrap';

const ArticleReader = ({ article, onRateArticle }) => {
  const handleRatingChange = (e) => {
    if (article) {
      onRateArticle(article.id, parseInt(e.target.value, 10));
    }
  };

  if (!article) {
    return (
      <Container className="d-flex flex-column align-items-center justify-content-center h-100 p-4">
        <div className="text-center text-muted">
          <h5>Aucun article sélectionné</h5>
          <p>Veuillez sélectionner un article dans la liste pour le lire.</p>
        </div>
      </Container>
    );
  }

  return (
    <Container className="p-4 h-100 d-flex flex-column">
      <Card className="border-0 flex-grow-1">
        <Card.Body className="p-0">
          <h3 className="mb-3">{article.title}</h3>
          
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div className="text-muted">
              <small>Source: {article.source}</small>
            </div>
            <div className="text-muted">
              <small>Date: {article.date}</small>
            </div>
          </div>
          
          <div className="mb-4">
            {article.content}
          </div>
          
          {article.published && (
            <div className="alert alert-success mt-3">
              <strong>Publié sur LinkedIn</strong> le {article.published_date}
            </div>
          )}
        </Card.Body>
      </Card>
      
      <Card className="mt-3">
        <Card.Body>
          <h5 className="mb-3">Noter cet article</h5>
          <Form.Group>
            <div className="d-flex align-items-center">
              <Form.Label className="me-3 mb-0">Note:</Form.Label>
              <Form.Select 
                value={article.rating || 0} 
                onChange={handleRatingChange}
                style={{ width: '100px' }}
              >
                <option value="0">Sélectionner</option>
                <option value="1">1 ★</option>
                <option value="2">2 ★★</option>
                <option value="3">3 ★★★</option>
                <option value="4">4 ★★★★</option>
                <option value="5">5 ★★★★★</option>
              </Form.Select>
            </div>
          </Form.Group>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default ArticleReader;
