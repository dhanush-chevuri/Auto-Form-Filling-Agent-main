import React from 'react';
import { Form } from 'react-bootstrap';

const FormInput = ({ value, onChange }) => {
  return (
    <div className="h-100">
      <h5 className="mb-3">🔗 Google Form URL</h5>
      <div className="d-flex flex-column h-100">
        <Form.Control
          type="url"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="https://docs.google.com/forms/d/..."
          size="lg"
          className="mb-3"
          list="form-url-history"
        />
        <datalist id="form-url-history">
          {/* Browser will automatically populate with previous entries */}
        </datalist>
        <div className="flex-grow-1 d-flex align-items-center">
          <small className="text-muted">
            📝 Enter the Google Form URL where you want to auto-fill the information
          </small>
        </div>
      </div>
    </div>
  );
};

export default FormInput;