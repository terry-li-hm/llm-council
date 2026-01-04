import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || responses.length === 0) {
    return null;
  }

  // Check if we have duplicate instances (same model appearing more than once)
  const hasDuplicates = responses.some((resp, idx) =>
    responses.findIndex(r => r.model === resp.model) !== idx
  );

  // Format tab label: include instance number if there are duplicates
  const formatTabLabel = (resp) => {
    const modelName = resp.model.split('/')[1] || resp.model;
    if (hasDuplicates && resp.instance) {
      return `${modelName} (${resp.instance})`;
    }
    return modelName;
  };

  // Format full model name for display
  const formatModelName = (resp) => {
    if (hasDuplicates && resp.instance) {
      return `${resp.model} (instance ${resp.instance})`;
    }
    return resp.model;
  };

  return (
    <div className="stage stage1">
      <h3 className="stage-title">Stage 1: Individual Responses</h3>

      <div className="tabs">
        {responses.map((resp, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {formatTabLabel(resp)}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="model-name">{formatModelName(responses[activeTab])}</div>
        <div className="response-text markdown-content">
          <ReactMarkdown>{responses[activeTab].response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
