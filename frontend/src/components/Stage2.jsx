import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage2.css';
import { extractReasoningText } from '../utils/reasoning';

// Helper to get model info from labelToModel (handles both old string format and new object format)
function getModelInfo(labelToModel, label) {
  if (!labelToModel || !labelToModel[label]) return null;
  const value = labelToModel[label];
  // Handle both old format (string) and new format (object with model/instance)
  if (typeof value === 'string') {
    return { model: value, instance: 1 };
  }
  return value;
}

// Check if labelToModel has any duplicate instances
function hasDuplicateInstances(labelToModel) {
  if (!labelToModel) return false;
  const models = Object.values(labelToModel).map(v =>
    typeof v === 'string' ? v : v.model
  );
  return models.some((m, idx) => models.indexOf(m) !== idx);
}

// Format model name with optional instance number
function formatModelWithInstance(modelInfo, showInstance) {
  if (!modelInfo) return 'Unknown';
  const shortName = modelInfo.model.split('/')[1] || modelInfo.model;
  if (showInstance && modelInfo.instance) {
    return `${shortName} (${modelInfo.instance})`;
  }
  return shortName;
}

function deAnonymizeText(text, labelToModel) {
  if (!labelToModel) return text;

  const showInstance = hasDuplicateInstances(labelToModel);
  let result = text;
  // Replace each "Response X" with the actual model name
  // Using string split/join to avoid regex issues with special characters
  Object.entries(labelToModel).forEach(([label, value]) => {
    const modelInfo = typeof value === 'string' ? { model: value, instance: 1 } : value;
    const displayName = formatModelWithInstance(modelInfo, showInstance);
    result = result.split(label).join(`**${displayName}**`);
  });
  return result;
}

export default function Stage2({ rankings, labelToModel, aggregateRankings }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!rankings || rankings.length === 0) {
    return null;
  }

  // Check if we have duplicate instances (same model appearing more than once)
  const rankerHasDuplicates = rankings.some((rank, idx) =>
    rankings.findIndex(r => r.model === rank.model) !== idx
  );

  const showInstanceInLabels = hasDuplicateInstances(labelToModel);

  // Format ranker tab label
  const formatRankerTabLabel = (rank) => {
    const modelName = rank.model.split('/')[1] || rank.model;
    if (rankerHasDuplicates && rank.instance) {
      return `${modelName} (${rank.instance})`;
    }
    return modelName;
  };

  // Format ranker full model name
  const formatRankerModelName = (rank) => {
    if (rankerHasDuplicates && rank.instance) {
      return `${rank.model} (instance ${rank.instance})`;
    }
    return rank.model;
  };

  return (
    <div className="stage stage2">
      <h3 className="stage-title">Stage 2: Peer Rankings</h3>

      <h4>Raw Evaluations</h4>
      <p className="stage-description">
        Each model evaluated all responses (anonymized as Response A, B, C, etc.) and provided rankings.
        Below, model names are shown in <strong>bold</strong> for readability, but the original evaluation used anonymous labels.
      </p>

      <div className="tabs">
        {rankings.map((rank, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {formatRankerTabLabel(rank)}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="ranking-model">
          {formatRankerModelName(rankings[activeTab])}
        </div>

        {extractReasoningText(rankings[activeTab].reasoning_details) && (
          <details className="thinking-section">
            <summary>Show reasoning process</summary>
            <div className="thinking-content markdown-content">
              <ReactMarkdown>
                {extractReasoningText(rankings[activeTab].reasoning_details)}
              </ReactMarkdown>
            </div>
          </details>
        )}

        <div className="ranking-content markdown-content">
          <ReactMarkdown>
            {deAnonymizeText(rankings[activeTab].ranking, labelToModel)}
          </ReactMarkdown>
        </div>

        {rankings[activeTab].parsed_ranking &&
         rankings[activeTab].parsed_ranking.length > 0 && (
          <div className="parsed-ranking">
            <strong>Extracted Ranking:</strong>
            <ol>
              {rankings[activeTab].parsed_ranking.map((label, i) => {
                const modelInfo = getModelInfo(labelToModel, label);
                return (
                  <li key={i}>
                    {modelInfo
                      ? formatModelWithInstance(modelInfo, showInstanceInLabels)
                      : label}
                  </li>
                );
              })}
            </ol>
          </div>
        )}
      </div>

      {aggregateRankings && aggregateRankings.length > 0 && (
        <div className="aggregate-rankings">
          <h4>Aggregate Rankings (Street Cred)</h4>
          <p className="stage-description">
            Combined results across all peer evaluations (lower score is better):
          </p>
          <div className="aggregate-list">
            {aggregateRankings.map((agg, index) => {
              const modelName = agg.model.split('/')[1] || agg.model;
              const displayName = agg.instance && agg.instance > 1
                ? `${modelName} (${agg.instance})`
                : (showInstanceInLabels && agg.instance ? `${modelName} (${agg.instance})` : modelName);
              return (
                <div key={index} className="aggregate-item">
                  <span className="rank-position">#{index + 1}</span>
                  <span className="rank-model">
                    {displayName}
                  </span>
                  <span className="rank-score">
                    Avg: {agg.average_rank.toFixed(2)}
                  </span>
                  <span className="rank-count">
                    ({agg.rankings_count} votes)
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
