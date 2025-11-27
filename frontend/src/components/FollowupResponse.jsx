import ReactMarkdown from 'react-markdown';
import './FollowupResponse.css';
import { extractReasoningText } from '../utils/reasoning';

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
