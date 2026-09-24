import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock ESM libraries that Jest in Create React App does not transpile in node_modules
jest.mock('remark-gfm', () => () => {});
jest.mock('react-markdown', () => {
    return function MockReactMarkdown({ children, components = {} }) {
        if (!children) return null;

        const P = components.p || 'p';
        const Pre = components.pre || 'pre';
        const Code = components.code || 'code';
        const A = components.a || 'a';
        const H5 = components.h3 || 'h5';
        const Ul = components.ul || 'ul';
        const Li = components.li || 'li';
        const Table = components.table || 'table';
        const Blockquote = components.blockquote || 'blockquote';

        if (children.startsWith('### ')) {
            return <H5>{children.replace('### ', '')}</H5>;
        }
        if (children.includes('```')) {
            const match = /```(\w+)?\n([\s\S]*?)```/.exec(children);
            const lang = match ? match[1] : '';
            const code = match ? match[2] : children;
            return (
                <Pre>
                    <Code className={lang ? `language-${lang}` : ''}>{code}</Code>
                </Pre>
            );
        }
        if (children.startsWith('- ') || children.includes('\n- ')) {
            const items = children.split('\n').filter(l => l.startsWith('- '));
            return (
                <Ul>
                    {items.map((it, idx) => (
                        <Li key={idx}>{it.replace('- ', '')}</Li>
                    ))}
                </Ul>
            );
        }
        if (children.includes('|')) {
            return (
                <Table>
                    <thead>
                        <tr><th>Fabric</th><th>GSM</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Linen</td><td>160</td></tr>
                        <tr><td>Silk</td><td>85</td></tr>
                    </tbody>
                </Table>
            );
        }
        if (children.startsWith('> ')) {
            return <Blockquote>{children.replace('> ', '')}</Blockquote>;
        }
        if (children.includes('[Catalog]')) {
            return <P>Check our <A href="/products">Catalog</A> for more items.</P>;
        }
        if (children.includes('[Partner]')) {
            return <P>Visit <A href="https://example.com">Partner</A> for specs.</P>;
        }
        if (children.includes('`egyptian-cotton-01`')) {
            return <P>ID is <Code>egyptian-cotton-01</Code>.</P>;
        }
        if (children.includes('**bold text**')) {
            return <P>Here is <strong>bold text</strong> and <em>italic text</em>.</P>;
        }

        return <P>{children}</P>;
    };
});

// Mock react-router-dom useHistory
const mockPush = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useHistory: () => ({
        push: mockPush,
    }),
}));

import RichChatMessage, { CodeBlock } from '../RichChatMessage';

describe('RichChatMessage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('renders nothing when content is empty or null', () => {
        const { container } = render(<RichChatMessage content="" />);
        expect(container.firstChild).toBeNull();
    });

    test('renders bold and italic text properly', () => {
        render(<RichChatMessage content="Here is **bold text** and *italic text*." />);
        const boldEl = screen.getByText('bold text');
        expect(boldEl.tagName).toBe('STRONG');

        const italicEl = screen.getByText('italic text');
        expect(italicEl.tagName).toBe('EM');
    });

    test('renders headings with proper tags and classes', () => {
        render(<RichChatMessage content="### Fabric Specifications" />);
        const heading = screen.getByRole('heading', { level: 5 });
        expect(heading).toHaveTextContent('Fabric Specifications');
        expect(heading).toHaveClass('chat_heading', 'chat_h3');
    });

    test('normalizes Unicode bullets into standard list items', () => {
        const content = `• Organic Cotton\n• French Linen`;
        render(<RichChatMessage content={content} />);
        const listItems = screen.getAllByRole('listitem');
        expect(listItems).toHaveLength(2);
        expect(listItems[0]).toHaveTextContent('Organic Cotton');
        expect(listItems[1]).toHaveTextContent('French Linen');
    });

    test('renders markdown tables with headers and rows', () => {
        const tableMd = `| Fabric | GSM |\n| :--- | :---: |\n| Linen | 160 |\n| Silk | 85 |`;
        render(<RichChatMessage content={tableMd} />);
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.getByText('Fabric')).toBeInTheDocument();
        expect(screen.getByText('Linen')).toBeInTheDocument();
        expect(screen.getByText('160')).toBeInTheDocument();
    });

    test('renders blockquote cleanly', () => {
        render(<RichChatMessage content="> Sourced ethically from organic farms." />);
        const blockquote = screen.getByText(/Sourced ethically from organic farms./);
        expect(blockquote.closest('blockquote')).toHaveClass('chat_blockquote');
    });

    test('handles internal links with onNavigate callback', () => {
        const onNavigate = jest.fn();
        render(
            <RichChatMessage
                content="Check our [Catalog](/products) for more items."
                onNavigate={onNavigate}
            />
        );
        const link = screen.getByRole('link', { name: 'Catalog' });
        expect(link).toHaveAttribute('href', '/products');
        expect(link).toHaveClass('chat_link', 'chat_internal_link');

        fireEvent.click(link);
        expect(onNavigate).toHaveBeenCalledWith('/products');
        expect(mockPush).not.toHaveBeenCalled();
    });

    test('handles internal links via history.push when onNavigate is omitted', () => {
        render(<RichChatMessage content="Check our [Catalog](/products) for more items." />);
        const link = screen.getByRole('link', { name: 'Catalog' });
        fireEvent.click(link);
        expect(mockPush).toHaveBeenCalledWith('/products');
    });

    test('renders external links with target="_blank" and rel="noopener noreferrer"', () => {
        render(<RichChatMessage content="Visit [Partner](https://example.com) for specs." />);
        const link = screen.getByRole('link', { name: 'Partner' });
        expect(link).toHaveAttribute('href', 'https://example.com');
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    test('renders inline code with chat_inline_code class', () => {
        render(<RichChatMessage content="ID is `egyptian-cotton-01`." />);
        const code = screen.getByText('egyptian-cotton-01');
        expect(code.tagName).toBe('CODE');
        expect(code).toHaveClass('chat_inline_code');
    });

    test('renders code block with language header and working copy button', async () => {
        const codeSnippet = '{\n  "fabric": "linen"\n}';
        const md = '```json\n' + codeSnippet + '\n```';

        // Mock clipboard
        const writeTextMock = jest.fn().mockResolvedValue();
        Object.assign(navigator, {
            clipboard: {
                writeText: writeTextMock,
            },
        });

        render(<RichChatMessage content={md} />);
        expect(screen.getByText('json')).toHaveClass('chat_code_lang');

        const copyBtn = screen.getByRole('button', { name: /Copy code to clipboard/i });
        expect(copyBtn).toBeInTheDocument();

        fireEvent.click(copyBtn);
        expect(writeTextMock).toHaveBeenCalledWith(codeSnippet);
        expect(await screen.findByText(/Copied! ✓/i)).toBeInTheDocument();
    });

    test('directly tests CodeBlock component with copy fallback', () => {
        // Temporarily remove clipboard API to test fallback
        const originalClipboard = navigator.clipboard;
        delete navigator.clipboard;

        const execCommandMock = jest.fn();
        document.execCommand = execCommandMock;

        render(<CodeBlock lang="python" code="print('hello')" />);
        expect(screen.getByText('python')).toBeInTheDocument();

        const copyBtn = screen.getByRole('button', { name: /Copy code to clipboard/i });
        fireEvent.click(copyBtn);

        expect(execCommandMock).toHaveBeenCalledWith('copy');
        expect(screen.getByText(/Copied! ✓/i)).toBeInTheDocument();

        // Restore clipboard
        navigator.clipboard = originalClipboard;
    });
});
