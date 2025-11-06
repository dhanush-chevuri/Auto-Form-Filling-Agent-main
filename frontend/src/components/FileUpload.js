import React, { useCallback } from 'react';
import { Card, Badge } from 'react-bootstrap';
import { useDropzone } from 'react-dropzone';

const FileUpload = ({ onFileSelect, selectedFile }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: false
  });

  return (
    <div>
      <h5 className="mb-3">📄 Upload Resume</h5>
      <Card 
        {...getRootProps()} 
        className={`text-center p-4 border-2 border-dashed h-100 ${
          isDragActive ? 'border-primary bg-light' : 'border-secondary'
        }`}
        style={{ cursor: 'pointer', minHeight: '200px' }}
      >
        <input {...getInputProps()} />
        <Card.Body className="d-flex flex-column justify-content-center">
          {selectedFile ? (
            <div>
              <div className="mb-3">
                <i className="bi bi-file-earmark-check text-success" style={{ fontSize: '3rem' }}></i>
              </div>
              <h6 className="text-success">✓ {selectedFile.name}</h6>
              <Badge bg="secondary">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</Badge>
            </div>
          ) : (
            <div>
              <div className="mb-3">
                <i className="bi bi-cloud-upload text-muted" style={{ fontSize: '3rem' }}></i>
              </div>
              {isDragActive ? (
                <p className="text-primary mb-0">Drop the resume file here...</p>
              ) : (
                <div>
                  <p className="mb-2">Drag & drop a resume file here, or click to select</p>
                  <small className="text-muted">Supported: PDF, DOCX, TXT</small>
                </div>
              )}
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default FileUpload;