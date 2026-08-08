import React, { useState, useEffect, useRef } from 'react';
import './AIAssistant.scss';
import { sendChatMessage } from '../../Api/ai';

export default function AIAssistant() {
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState('');
    const [chatHistory, setChatHistory] = useState([
        { role: 'assistant', content: 'Hello! I am your Ankh Textile Assistant. Ask me anything about our fabrics, compare specifications, or describe your needs (e.g., skin sensitivities, climate preference) and I will suggest the perfect material!' }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatHistory, isLoading]);

    const handleSend = async (e) => {
        if (e) e.preventDefault();
        if (!message.trim() || isLoading) return;

        const userMessage = message;
        setMessage('');
        const updatedHistory = [...chatHistory, { role: 'user', content: userMessage }];
        setChatHistory(updatedHistory);
        setIsLoading(true);

        try {
            const data = await sendChatMessage(
                userMessage,
                updatedHistory.slice(1, -1) // exclude intro and latest user message
            );
            setChatHistory(prev => [...prev, { role: 'assistant', content: data.response, recommended: data.recommended_products }]);
        } catch (error) {
            console.error('AI chat failed:', error);
            const content = error.status
                ? 'Sorry, I encountered an issue processing your query.'
                : 'Failed to connect to AI server. Please make sure the backend is running.';
            setChatHistory(prev => [...prev, { role: 'assistant', content }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="ai_assistant_root">
            {/* Floating Trigger Bubble */}
            <button 
                className={`ai_bubble_trigger ${isOpen ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                aria-label="Toggle AI assistant"
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {/* Chat Panel Container */}
            {isOpen && (
                <div className="ai_chat_panel">
                    <div className="ai_panel_header">
                        <h3>Ankh Shopping Assistant</h3>
                        <p>Locally powered by Qwen2.5</p>
                    </div>

                    <div className="ai_messages_container">
                        {chatHistory.map((chat, idx) => (
                            <div key={idx} className={`ai_message_wrapper ${chat.role}`}>
                                <div className="ai_message_bubble">
                                    <p>{chat.content}</p>
                                    
                                    {/* Render references/recommendation links */}
                                    {chat.recommended && chat.recommended.length > 0 && (
                                        <div className="ai_recommendation_links">
                                            <p className="rec_title">Suggested Products:</p>
                                            <div className="rec_chips">
                                                {chat.recommended.map((prodId, rIdx) => (
                                                    <a 
                                                        key={rIdx} 
                                                        href={`/products/${prodId}`}
                                                        className="rec_chip_link"
                                                        onClick={() => setIsOpen(false)}
                                                    >
                                                        🔍 {prodId}
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="ai_message_wrapper assistant">
                                <div className="ai_message_bubble loading">
                                    <span className="dot"></span>
                                    <span className="dot"></span>
                                    <span className="dot"></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <form className="ai_input_form" onSubmit={handleSend}>
                        <input 
                            type="text" 
                            placeholder="Type a message..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            disabled={isLoading}
                        />
                        <button type="submit" className="send_btn" disabled={isLoading || !message.trim()}>
                            ➔
                        </button>
                    </form>
                </div>
            )}
        </div>
    );
}
