import { post } from './client';

/**
 * @param {string} message
 * @param {Array<{role: string, content: string}>} chatHistory
 */
export const sendChatMessage = (message, chatHistory = []) =>
    post('/api/ai/chat', { message, chat_history: chatHistory });
