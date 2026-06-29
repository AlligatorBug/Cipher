import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function AgentChat() {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    async function sendMessage() {
        if (!input.trim() || loading) return;

        const question = input;
        setInput('');
        setLoading(true);

        setMessages(prev => [...prev, { role: 'user', content: question }]);
        setMessages(prev => [...prev, { role: 'agent', content: '', tools: [] }]);

        const token = localStorage.getItem('cipher_token');
        const response = await fetch(`${process.env.REACT_APP_API_URL}/agent/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ question })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const lines = decoder.decode(value).split('\n');
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const event = JSON.parse(line.slice(6));

                if (event.type === 'token') {
                    setMessages(prev => {
                        const updated = [...prev];
                        updated[updated.length - 1].content = event.content;
                        return updated;
                    });
                } else if (event.type === 'tool') {
                    setMessages(prev => {
                        const updated = [...prev];
                        const last = updated[updated.length - 1];
                        if (!last.tools.includes(event.name)) {
                            last.tools = [...last.tools, event.name];
                        }
                        return updated;
                    });
                }
            }
        }
        setLoading(false);
    }

    function cleanToolName(name) {
        return name.replace(/_tool$/, '').replace(/_/g, ' ');
    }

    return (
        <>
        <style>{`
            @keyframes pulse {
                0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
                40% { opacity: 1; transform: scale(1); }
            }
            .thinking-dot {
                width: 6px;
                height: 6px;
                background: #D4537E;
                border-radius: 50%;
                display: inline-block;
                margin: 0 2px;
                animation: pulse 1.4s ease-in-out infinite;
            }
            .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
            .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
            .agent-msg-content { width: 100%; overflow: hidden; }
            .agent-msg-content p { margin: 0 0 6px 0; word-break: break-word; }
            .agent-msg-content p:last-child { margin: 0; }
            .agent-msg-content ul { margin: 4px 0; padding-left: 18px; }
            .agent-msg-content li { margin: 2px 0; word-break: break-word; }
            .agent-msg-content strong { font-weight: 600; color: #1a1a1a; }
        `}</style>

        {/* floating button */}
        <button onClick={() => setOpen(!open)} style={styles.fab}>
            {open ? '✕' : '✦'}
        </button>

        {/* chat window */}
        {open && (
            <div style={styles.window}>
                <div style={styles.header}>
                    <span>CipherAgent</span>
                    <span style={styles.headerSub}>your personal finance AI</span>
                </div>
                <div style={styles.messages}>
                    {messages.map((m, i) => (
                        <div key={i} style={m.role === 'user' ? styles.userMsg : styles.agentMsg}>
                            {m.role === 'agent' && m.tools.length > 0 && (
                                <div style={styles.pillRow}>
                                    {m.tools.map((t, j) => (
                                        <span key={j} style={styles.pill}>⚡ {cleanToolName(t)}</span>
                                    ))}
                                </div>
                            )}
                            {m.role === 'agent' && !m.content && loading && i === messages.length - 1 ? (
                                <div style={{ padding: '4px 2px' }}>
                                    <span className="thinking-dot" />
                                    <span className="thinking-dot" />
                                    <span className="thinking-dot" />
                                </div>
                            ) : m.role === 'agent' ? (
                                <div className="agent-msg-content">
                                    <ReactMarkdown>{m.content}</ReactMarkdown>
                                </div>
                            ) : (
                                <div>{m.content}</div>
                            )}
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
                <div style={styles.inputRow}>
                    <input
                        style={styles.input}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && sendMessage()}
                        placeholder="Ask anything about your spending..."
                        disabled={loading}
                    />
                    <button style={styles.send} onClick={sendMessage} disabled={loading}>↑</button>
                </div>
            </div>
        )}
        </>
    );
}

const styles = {
    fab: {
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        width: '48px',
        height: '48px',
        borderRadius: '50%',
        background: '#D4537E',
        color: 'white',
        fontSize: '18px',
        border: 'none',
        cursor: 'pointer',
        zIndex: 1000,
        boxShadow: '0 2px 8px rgba(212,83,126,0.35)',
    },
    window: {
        position: 'fixed',
        bottom: '84px',
        right: '24px',
        width: '440px',
        height: '620px',
        background: '#ffffff',
        borderRadius: '16px',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
        border: '1px solid #ede8e3',
        overflow: 'hidden',
    },
    header: {
        padding: '14px 16px',
        borderBottom: '1px solid #ede8e3',
        background: '#faf8f5',
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
    },
    headerSub: {
        fontSize: '11px',
        color: '#aaa',
        fontWeight: '400',
    },
    messages: {
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        background: '#faf8f5',
    },
    userMsg: {
        alignSelf: 'flex-end',
        background: '#D4537E',
        color: 'white',
        padding: '9px 13px',
        borderRadius: '12px 12px 2px 12px',
        maxWidth: '72%',
        fontSize: '13px',
        lineHeight: '1.5',
        wordBreak: 'break-word',
    },
    agentMsg: {
        alignSelf: 'flex-start',
        background: '#ffffff',
        color: '#1a1a1a',
        padding: '9px 13px',
        borderRadius: '12px',
        maxWidth: '90%',
        fontSize: '13px',
        lineHeight: '1.5',
        border: '1px solid #ede8e3',
        wordBreak: 'break-word',
        overflowWrap: 'break-word',
    },
    pillRow: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '4px',
        marginBottom: '7px',
    },
    pill: {
        display: 'inline-block',
        background: '#fdf0f4',
        color: '#D4537E',
        fontSize: '10px',
        padding: '2px 8px',
        borderRadius: '999px',
        border: '1px solid #f5cdd9',
    },
    inputRow: {
        display: 'flex',
        padding: '12px',
        borderTop: '1px solid #ede8e3',
        gap: '8px',
        background: '#ffffff',
    },
    input: {
        flex: 1,
        background: '#faf8f5',
        border: '1px solid #ede8e3',
        borderRadius: '8px',
        padding: '9px 12px',
        color: '#1a1a1a',
        outline: 'none',
        fontSize: '13px',
    },
    send: {
        background: '#D4537E',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        padding: '9px 14px',
        cursor: 'pointer',
        fontSize: '15px',
    },
};
