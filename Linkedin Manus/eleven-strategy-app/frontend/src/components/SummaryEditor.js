import React from 'react';
import { Container, Card, Button, Form, Spinner } from 'react-bootstrap';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

const SummaryEditor = ({ article, summary, onGenerateSummary, onSummaryChange, onPublishToLinkedIn, loading }) => {
  if (!article) {
    return (
      <Container className="d-flex flex-column align-items-center justify-content-center h-100 p-4">
        <div className="text-center text-muted">
          <h5>Aucun article sélectionné</h5>
          <p>Veuillez sélectionner un article pour générer un résumé.</p>
        </div>
      </Container>
    );
  }

  return (
    <Container className="p-4 h-100 d-flex flex-column">
      <Card className="border-0 flex-grow-1">
        <Card.Body className="p-0">
          <h4 className="mb-3">Résumé et Publication</h4>
          
          <div className="mb-3 d-flex justify-content-between">
            <Button 
              variant="primary" 
              onClick={onGenerateSummary}
              disabled={loading || !article}
            >
              {loading ? (
                <>
                  <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                  <span className="ms-2">Génération...</span>
                </>
              ) : (
                'Générer un résumé'
              )}
            </Button>
          </div>
          
          <div className="mb-4">
            <Form.Group>
              <Form.Label>Résumé pour LinkedIn</Form.Label>
              <div style={{ height: '300px' }}>
                <ReactQuill 
                  theme="snow" 
                  value={summary} 
                  onChange={onSummaryChange}
                  style={{ height: '250px' }}
                />
              </div>
            </Form.Group>
          </div>
          
          <Button 
            variant="success" 
            className="w-100 mt-3"
            disabled={loading || !summary || article.published}
            onClick={onPublishToLinkedIn}
          >
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                <span className="ms-2">Publication en cours...</span>
              </>
            ) : article.published ? (
              'Déjà publié'
            ) : (
              'Publier sur LinkedIn'
            )}
          </Button>
          
          {article.published && (
            <div className="alert alert-success mt-3">
              <strong>Publié sur LinkedIn</strong> le {article.published_date}
            </div>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default SummaryEditor;
