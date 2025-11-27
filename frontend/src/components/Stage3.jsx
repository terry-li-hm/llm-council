import ReactMarkdown from 'react-markdown';
import './Stage3.css';
import { extractReasoningText } from '../utils/reasoning';

export default function Stage3({ finalResponse }) {
  if (!finalResponse) {
    return null;
  }

  // Get reasoning text from either reasoning_details or thinking
  const reasoningText = extractReasoningText(finalResponse.reasoning_details)
    || finalResponse.thinking;

  return (
    <div className="stage stage3">
      <h3 className="stage-title">Stage 3: Final Council Answer</h3>
      <div className="final-response">
        <div className="chairman-label">
          Chairman: {finalResponse.model.split('/')[1] || finalResponse.model}
        </div>
        {reasoningText && (
          <details className="thinking-section">
            <summary>Show reasoning process</summary>
            <div className="thinking-content markdown-content">
              <ReactMarkdown>{reasoningText}</ReactMarkdown>
            </div>
          </details>
        )}
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
