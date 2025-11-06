import React from 'react';
import { Alert, ListGroup, Badge } from 'react-bootstrap';

const ResultDisplay = ({ result }) => {
  if (!result) return null;

  console.log('Result Display Data:', result);

  return (
    <div>
      {result.success ? (
        <Alert variant="success" className="shadow-sm">
          <Alert.Heading className="h5">
            <i className="bi bi-check-circle-fill me-2"></i>
            Form Submitted Successfully!
          </Alert.Heading>
          <p className="mb-2">
            <i className="bi bi-info-circle me-2"></i>
            Your form was submitted directly via API - no browser redirect needed!
          </p>
          {result.filled_fields && result.filled_fields.length > 0 && (
            <div className="mt-3">
              <p className="mb-2">
                <Badge bg="success" className="me-2">{result.filled_fields.length}</Badge>
                fields filled successfully
              </p>
              <ListGroup variant="flush">
                {result.filled_fields.map((field, index) => (
                  <ListGroup.Item key={index} className="px-0 py-1">
                    <i className="bi bi-check text-success me-2"></i>
                    {field}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </div>
          )}
          {result.message && (
            <p className="mb-0 mt-2">
              <small className="text-success">
                <i className="bi bi-lightning-fill me-1"></i>
                {result.message}
              </small>
            </p>
          )}
        </Alert>
      ) : (
        <Alert variant={result.ats_friendly === false ? "warning" : "danger"} className="shadow-sm">
          <Alert.Heading className="h5">
            <i className={`bi ${result.ats_friendly === false ? 'bi-file-earmark-x-fill' : 'bi-exclamation-triangle-fill'} me-2`}></i>
            {result.ats_friendly === false ? '⚠️ PDF is NOT ATS-Friendly' : 'Error Occurred'}
          </Alert.Heading>
          
          {result.ats_friendly === false ? (
            <div>
              <p className="mb-3 fw-bold">{result.message || 'Your resume cannot be read by ATS systems'}</p>
              {result.suggestions && result.suggestions.length > 0 && (
                <div>
                  <p className="mb-2 fw-semibold">How to fix:</p>
                  <ListGroup variant="flush" className="bg-transparent">
                    {result.suggestions.map((suggestion, index) => (
                      <ListGroup.Item key={index} className="px-0 py-2 bg-transparent border-0">
                        <i className="bi bi-arrow-right-circle text-warning me-2"></i>
                        {suggestion}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </div>
              )}
              <div className="alert alert-light mt-3 mb-0">
                <small>
                  <strong>💡 Quick Test:</strong> Open your PDF and try to select/copy text. 
                  If you can't select text, it's not ATS-friendly!
                </small>
              </div>
            </div>
          ) : (
            <div>
              {result.error && <p className="mb-0">{result.error}</p>}
            </div>
          )}
        </Alert>
      )}
    </div>
  );
};

export default ResultDisplay;