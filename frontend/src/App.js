import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Spinner } from 'react-bootstrap';
import FileUpload from './components/FileUpload';
import FormInput from './components/FormInput';
import ResultDisplay from './components/ResultDisplay';
import { fillForm } from './services/api';

function App() {
  const [file, setFile] = useState(null);
  const [formUrl, setFormUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load previous form URL from localStorage on component mount
  useEffect(() => {
    const savedFormUrl = localStorage.getItem('lastFormUrl');
    if (savedFormUrl) {
      setFormUrl(savedFormUrl);
    }
  }, []);

  // Save form URL to localStorage whenever it changes
  const handleFormUrlChange = (url) => {
    setFormUrl(url);
    if (url.trim()) {
      localStorage.setItem('lastFormUrl', url);
    }
  };

  const handleFillForm = async () => {
    if (!file || !formUrl) {
      setResult({ success: false, error: 'Please upload a resume and enter a form URL' });
      return;
    }

    setLoading(true);
    try {
      const response = await fillForm(file, formUrl);
      console.log('API Response:', response.data);
      // Backend now returns result directly
      setResult(response.data);
    } catch (error) {
      console.error('API Error:', error);
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="py-5">
      <Row className="justify-content-center">
        <Col lg={8}>
          <div className="text-center mb-5">
            <h1 className="display-4 text-primary mb-3">🤖 Auto Form Filling Agent</h1>
            <p className="lead text-muted">Upload your resume and provide a Google Form link to auto-submit it directly via API</p>
            <div className="alert alert-info border-0 bg-light">
              <small>
                <i className="bi bi-lightning-fill me-2"></i>
                <strong>Direct API Submission:</strong> No browser redirects - forms are filled and submitted automatically!
              </small>
            </div>
          </div>
          
          <Card className="shadow-lg border-0">
            <Card.Body className="p-4">
              <Row className="g-4">
                <Col md={6}>
                  <FileUpload onFileSelect={setFile} selectedFile={file} />
                </Col>
                <Col md={6}>
                  <FormInput value={formUrl} onChange={handleFormUrlChange} />
                </Col>
              </Row>
              
              <div className="text-center mt-4">
                <Button 
                  onClick={handleFillForm} 
                  disabled={loading || !file || !formUrl}
                  variant="primary"
                  size="lg"
                  className="px-5"
                >
                  {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Processing...
                    </>
                  ) : (
                    '🚀 Submit Form Directly'
                  )}
                </Button>
              </div>
            </Card.Body>
          </Card>
          
          {result && (
            <div className="mt-4">
              <ResultDisplay result={result} />
            </div>
          )}
        </Col>
      </Row>
    </Container>
  );
}

export default App;