import { useState, useEffect } from 'react';
import './Settings.css';

export default function Settings({ isOpen, onClose, models, duplicateModels, onDuplicateModelsChange }) {
  const [localDuplicates, setLocalDuplicates] = useState(duplicateModels);

  // Sync local state when prop changes
  useEffect(() => {
    setLocalDuplicates(duplicateModels);
  }, [duplicateModels]);

  if (!isOpen) return null;

  const handleToggleModel = (model) => {
    setLocalDuplicates(prev => {
      if (prev.includes(model)) {
        return prev.filter(m => m !== model);
      } else {
        return [...prev, model];
      }
    });
  };

  const handleToggleAll = () => {
    if (localDuplicates.length === models.length) {
      setLocalDuplicates([]);
    } else {
      setLocalDuplicates([...models]);
    }
  };

  const handleSave = () => {
    onDuplicateModelsChange(localDuplicates);
    onClose();
  };

  const handleCancel = () => {
    setLocalDuplicates(duplicateModels);
    onClose();
  };

  const allSelected = models.length > 0 && localDuplicates.length === models.length;
  const someSelected = localDuplicates.length > 0 && localDuplicates.length < models.length;

  return (
    <div className="settings-overlay" onClick={handleCancel}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Council Settings</h2>
          <button className="settings-close-btn" onClick={handleCancel}>×</button>
        </div>

        <div className="settings-content">
          <div className="settings-section">
            <h3>Duplicate Instances</h3>
            <p className="settings-description">
              Select which models should be queried twice to capture intra-model variance.
              This doubles the API cost for selected models but reveals how consistent their responses are.
            </p>

            <div className="model-toggles">
              <label className="model-toggle select-all">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={input => {
                    if (input) input.indeterminate = someSelected;
                  }}
                  onChange={handleToggleAll}
                />
                <span className="model-name">Select All</span>
              </label>

              <div className="model-list">
                {models.map(model => {
                  const shortName = model.split('/')[1] || model;
                  return (
                    <label key={model} className="model-toggle">
                      <input
                        type="checkbox"
                        checked={localDuplicates.includes(model)}
                        onChange={() => handleToggleModel(model)}
                      />
                      <span className="model-name">{shortName}</span>
                      <span className="model-full-name">{model}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="settings-footer">
          <button className="settings-btn settings-btn-secondary" onClick={handleCancel}>
            Cancel
          </button>
          <button className="settings-btn settings-btn-primary" onClick={handleSave}>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
