import ReactMarkdown from 'react-markdown';
import './FollowupResponse.css';

// Extract readable text from reasoning_details array
function extractReasoningText(reasoningDetails) {
  if (!reasoningDetails || !Array.isArray(reasoningDetails)) {
    return null;
  }

  const textParts = reasoningDetails
    .filter(detail => detail.type === 'reasoning.text' && detail.text)
    .map(detail => detail.text);

  return textParts.length > 0 ? textParts.join('\n\n') : null;
}

export default function FollowupResponse({ response }) {
  if (!response) {
    return null;
  }

  const reasoningText = extractReasoningText(response.reasoning_details)
    || response.thinking;

  return (
    <div className="followup-response">
      <div className="followup-header">
        <span className="followup-badge">Follow-up</span>
        <span className="followup-model">
          Chairman: {response.model.split('/')[1] || response.model}
        </span>
      </div>
      {reasoningText && (
        <details className="thinking-section">
          <summary>Show reasoning process</summary>
          <div className="thinking-content markdown-content">
            <ReactMarkdown>{reasoningText}</ReactMarkdown>
          </div>
        </details>
      )}
      <div className="followup-text markdown-content">
        <ReactMarkdown>{response.response}</ReactMarkdown>
      </div>
    </div>
  );
}
