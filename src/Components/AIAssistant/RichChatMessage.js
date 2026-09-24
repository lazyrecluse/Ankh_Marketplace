import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function CodeBlock({ lang, code }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        const textToCopy = code || '';
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard
                .writeText(textToCopy)
                .then(() => {
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                })
                .catch(() => {
                    fallbackCopy(textToCopy);
                });
        } else {
            fallbackCopy(textToCopy);
        }
    };

    const fallbackCopy = (text) => {
        try {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            textarea.style.top = '-9999px';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Copy failed:', err);
        }
    };

    const displayLang = lang || 'code';

    return (
        <div className="chat_code_container">
            <div className="chat_code_header">
                <span className="chat_code_lang">{displayLang}</span>
                <button
                    type="button"
                    className={`chat_code_copy_btn ${copied ? 'copied' : ''}`}
                    onClick={handleCopy}
                    aria-label={copied ? 'Code copied' : 'Copy code to clipboard'}
                >
                    {copied ? 'Copied! ✓' : 'Copy'}
                </button>
            </div>
            <pre className="chat_code_block">
                <code className={`language-${displayLang}`}>{code}</code>
            </pre>
        </div>
    );
}

function PreBlock({ children }) {
    const codeElement = React.isValidElement(children) ? children : null;
    const className = codeElement?.props?.className || '';
    const match = /language-(\w+)/.exec(className);
    const lang = match ? match[1] : 'code';
    const rawCode = String(codeElement?.props?.children || '').replace(/\n$/, '');

    return <CodeBlock lang={lang} code={rawCode} />;
}

export default function RichChatMessage({ content, role = 'assistant', onNavigate }) {
    const history = useHistory();

    if (!content) return null;

    // Normalize Unicode bullets (• ) to standard markdown list dashes (- )
    const normalizedContent = content.replace(/^(\s*)•\s+/gm, '$1- ');

    const components = {
        pre: PreBlock,
        code: ({ className, children, ...props }) => (
            <code className={className || 'chat_inline_code'} {...props}>
                {children}
            </code>
        ),
        a: ({ href, children, ...props }) => {
            const isInternal = href && href.startsWith('/');
            if (isInternal) {
                return (
                    <a
                        href={href}
                        className="chat_link chat_internal_link"
                        onClick={(e) => {
                            e.preventDefault();
                            if (onNavigate) {
                                onNavigate(href);
                            } else if (history) {
                                history.push(href);
                            }
                        }}
                        {...props}
                    >
                        {children}
                    </a>
                );
            }
            return (
                <a
                    href={href}
                    className="chat_link"
                    target="_blank"
                    rel="noopener noreferrer"
                    {...props}
                >
                    {children}
                </a>
            );
        },
        table: ({ children, ...props }) => (
            <div className="chat_table_wrapper">
                <table className="chat_table" {...props}>
                    {children}
                </table>
            </div>
        ),
        ul: ({ children, ...props }) => <ul className="chat_ul" {...props}>{children}</ul>,
        ol: ({ children, ...props }) => <ol className="chat_ol" {...props}>{children}</ol>,
        li: ({ children, ...props }) => <li className="chat_li" {...props}>{children}</li>,
        blockquote: ({ children, ...props }) => <blockquote className="chat_blockquote" {...props}>{children}</blockquote>,
        h1: ({ children, ...props }) => <h4 className="chat_heading chat_h1" {...props}>{children}</h4>,
        h2: ({ children, ...props }) => <h4 className="chat_heading chat_h2" {...props}>{children}</h4>,
        h3: ({ children, ...props }) => <h5 className="chat_heading chat_h3" {...props}>{children}</h5>,
        h4: ({ children, ...props }) => <h5 className="chat_heading chat_h4" {...props}>{children}</h5>,
        h5: ({ children, ...props }) => <h6 className="chat_heading chat_h5" {...props}>{children}</h6>,
        h6: ({ children, ...props }) => <h6 className="chat_heading chat_h6" {...props}>{children}</h6>,
        p: ({ children, ...props }) => <p className="chat_p" {...props}>{children}</p>,
        hr: (props) => <hr className="chat_hr" {...props} />,
    };

    return (
        <div className={`rich_chat_content ${role}`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
                {normalizedContent}
            </ReactMarkdown>
        </div>
    );
}
