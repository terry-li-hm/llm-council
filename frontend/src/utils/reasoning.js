/**
 * Shared utilities for handling reasoning/thinking content from LLM responses.
 */

/**
 * Extract readable text from reasoning_details array.
 * Works with OpenRouter's reasoning_details format.
 *
 * @param {Array} reasoningDetails - Array of reasoning detail objects
 * @returns {string|null} - Joined reasoning text or null if none found
 */
export function extractReasoningText(reasoningDetails) {
  if (!reasoningDetails || !Array.isArray(reasoningDetails)) {
    return null;
  }

  const textParts = reasoningDetails
    .filter(detail => detail.type === 'reasoning.text' && detail.text)
    .map(detail => detail.text);

  return textParts.length > 0 ? textParts.join('\n\n') : null;
}
