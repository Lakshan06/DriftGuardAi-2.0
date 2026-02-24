import { useState } from 'react';
import '../styles/Modal.css';

interface ModelFormData {
  model_name: string;
  version: string;
  description: string;
  training_accuracy: string;
  fairness_baseline: string;
  schema_definition: string;
  deployment_status: string;
}

interface ModelRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: ModelFormData) => Promise<void>;
}

const DEMO_TEMPLATE: ModelFormData = {
  model_name: 'fraud_detection_prod_v1',
  version: 'v1.0.0',
  description: 'Simulated production fraud detection model for governance demo',
  training_accuracy: '0.92',
  fairness_baseline: '0.85',
  schema_definition: JSON.stringify({
    transaction_amount: 'float',
    customer_age: 'int',
    gender: 'string',
    country: 'string',
    device_type: 'string'
  }, null, 2),
  deployment_status: 'draft'
};

export function ModelRegistrationModal({ isOpen, onClose, onSubmit }: ModelRegistrationModalProps) {
  const [formData, setFormData] = useState<ModelFormData>({
    model_name: '',
    version: '',
    description: '',
    training_accuracy: '',
    fairness_baseline: '',
    schema_definition: '',
    deployment_status: 'draft'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleUseDemoTemplate = () => {
    setFormData(DEMO_TEMPLATE);
    setError('');
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const validateForm = (): boolean => {
    if (!formData.model_name.trim()) {
      setError('Model name is required');
      return false;
    }
    if (!formData.version.trim()) {
      setError('Version is required');
      return false;
    }
    
    // Validate schema_definition JSON if provided
    if (formData.schema_definition.trim()) {
      try {
        JSON.parse(formData.schema_definition);
      } catch {
        setError('Schema definition must be valid JSON');
        return false;
      }
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await onSubmit(formData);
      // Reset form
      setFormData({
        model_name: '',
        version: '',
        description: '',
        training_accuracy: '',
        fairness_baseline: '',
        schema_definition: '',
        deployment_status: 'draft'
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to register model');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({
        model_name: '',
        version: '',
        description: '',
        training_accuracy: '',
        fairness_baseline: '',
        schema_definition: '',
        deployment_status: 'draft'
      });
      setError('');
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Register New Model</h2>
          <button 
            className="modal-close-btn" 
            onClick={handleClose}
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <div className="modal-body">
          {/* Demo Template Button */}
          <div className="demo-template-section">
            <button
              type="button"
              className="btn btn-secondary btn-demo-template"
              onClick={handleUseDemoTemplate}
              disabled={isSubmitting}
            >
              🎭 Use Simulated Demo Template
            </button>
            <p className="demo-template-hint">
              Pre-fills the form with a fraud detection demo model
            </p>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="model_name">
                Model Name <span className="required">*</span>
              </label>
              <input
                type="text"
                id="model_name"
                name="model_name"
                value={formData.model_name}
                onChange={handleChange}
                placeholder="e.g., fraud_detection_prod_v1"
                disabled={isSubmitting}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="version">
                Version <span className="required">*</span>
              </label>
              <input
                type="text"
                id="version"
                name="version"
                value={formData.version}
                onChange={handleChange}
                placeholder="e.g., v1.0.0"
                disabled={isSubmitting}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Brief description of the model"
                rows={3}
                disabled={isSubmitting}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="training_accuracy">Training Accuracy</label>
                <input
                  type="number"
                  id="training_accuracy"
                  name="training_accuracy"
                  value={formData.training_accuracy}
                  onChange={handleChange}
                  placeholder="0.0 - 1.0"
                  step="0.01"
                  min="0"
                  max="1"
                  disabled={isSubmitting}
                />
              </div>

              <div className="form-group">
                <label htmlFor="fairness_baseline">Fairness Baseline</label>
                <input
                  type="number"
                  id="fairness_baseline"
                  name="fairness_baseline"
                  value={formData.fairness_baseline}
                  onChange={handleChange}
                  placeholder="0.0 - 1.0"
                  step="0.01"
                  min="0"
                  max="1"
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="schema_definition">
                Schema Definition (JSON)
              </label>
              <textarea
                id="schema_definition"
                name="schema_definition"
                value={formData.schema_definition}
                onChange={handleChange}
                placeholder='{"feature_name": "data_type"}'
                rows={6}
                className="code-textarea"
                disabled={isSubmitting}
              />
              <p className="form-hint">
                Define the input features and their data types
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="deployment_status">Deployment Status</label>
              <select
                id="deployment_status"
                name="deployment_status"
                value={formData.deployment_status}
                onChange={handleChange}
                disabled={isSubmitting}
              >
                <option value="draft">Draft</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Registering...' : 'Register Model'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
