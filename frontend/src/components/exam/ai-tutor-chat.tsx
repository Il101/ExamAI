'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { chatApi, type ChatMessage } from '@/lib/api/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface AiTutorChatProps {
    topicId: string;
}

export function AiTutorChat({ topicId }: AiTutorChatProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Load chat history on mount
    useEffect(() => {
        loadHistory();
    }, [topicId]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadHistory = async () => {
        try {
            setIsLoadingHistory(true);
            const history = await chatApi.getHistory(topicId);
            setMessages(history);
        } catch (error) {
            console.error('Failed to load chat history:', error);
        } finally {
            setIsLoadingHistory(false);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        setIsLoading(true);

        // Optimistically add user message
        const tempUserMsg: ChatMessage = {
            id: 'temp-' + Date.now(),
            role: 'user',
            content: userMessage,
            created_at: new Date().toISOString(),
        };
        setMessages(prev => [...prev, tempUserMsg]);

        try {
            // Send message and get AI response
            const aiResponse = await chatApi.sendMessage(topicId, userMessage);

            // Replace temp message with real one and add AI response
            setMessages(prev => [
                ...prev.filter(m => m.id !== tempUserMsg.id),
                { ...tempUserMsg, id: aiResponse.id }, // Real user message
                aiResponse, // AI response
            ]);
        } catch (error) {
            console.error('Failed to send message:', error);
            // Remove temp message on error
            setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
            alert('Failed to send message. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleClear = async () => {
        if (!confirm('Clear all chat history for this topic?')) return;

        try {
            await chatApi.clearHistory(topicId);
            setMessages([]);
        } catch (error) {
            console.error('Failed to clear history:', error);
            alert('Failed to clear history. Please try again.');
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (isLoadingHistory) {
        return (
            <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[600px]">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 text-muted-foreground/60 space-y-4">
                        <div className="p-4 rounded-full bg-primary/5 mb-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary/40 to-violet-500/40 blur-lg absolute" />
                            <Send className="w-8 h-8 text-primary relative z-10" />
                        </div>
                        <div>
                            <p className="text-base font-medium text-foreground">AI Tutor is ready!</p>
                            <p className="text-sm">Ask about the topic, requesting flashcards, or a summary.</p>
                        </div>
                        <div className="flex flex-wrap justify-center gap-2 mt-4 max-w-sm">
                            {["Explain this topic", "Generate a quiz", "Key concepts"].map((suggestion) => (
                                <button
                                    key={suggestion}
                                    onClick={() => setInput(suggestion)}
                                    className="text-xs px-3 py-1.5 rounded-full bg-muted/50 hover:bg-muted transition-colors border border-border/50"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <>
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`relative max-w-[85%] sm:max-w-[75%] px-5 py-3 text-sm shadow-sm
                                    ${message.role === 'user'
                                            ? 'bg-gradient-to-br from-primary to-violet-600 text-white rounded-2xl rounded-tr-sm selection:bg-white/30'
                                            : 'bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800/50 text-foreground rounded-2xl rounded-tl-sm'
                                        }`}
                                >
                                    {message.role === 'user' ? (
                                        <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
                                    ) : (
                                        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0 prose-pre:border prose-pre:border-border/50 prose-pre:rounded-lg">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    code({ node, inline, className, children, ...props }: any) {
                                                        const match = /language-(\w+)/.exec(className || '');
                                                        return !inline && match ? (
                                                            <div className="overflow-hidden rounded-lg my-2">
                                                                <div className="flex items-center justify-between px-3 py-1 bg-zinc-950 text-xs text-zinc-400 border-b border-zinc-800">
                                                                    <span>{match[1]}</span>
                                                                </div>
                                                                <SyntaxHighlighter
                                                                    style={oneDark}
                                                                    language={match[1]}
                                                                    PreTag="div"
                                                                    customStyle={{ margin: 0, borderRadius: 0 }}
                                                                    {...props}
                                                                >
                                                                    {String(children).replace(/\n$/, '')}
                                                                </SyntaxHighlighter>
                                                            </div>
                                                        ) : (
                                                            <code className={`${className} bg-muted px-1.5 py-0.5 rounded text-xs font-mono`} {...props}>
                                                                {children}
                                                            </code>
                                                        );
                                                    },
                                                }}
                                            >
                                                {message.content}
                                            </ReactMarkdown>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Typing indicator */}
                        {isLoading && (
                            <div className="flex justify-start w-full">
                                <div className="bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800/50 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                                    <div className="flex space-x-1.5">
                                        <div className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 pt-2">
                <div className="relative flex items-end gap-2 bg-white dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 p-2 rounded-[24px] shadow-sm transition-all focus-within:ring-1 focus-within:ring-primary focus-within:border-primary/50">
                    <Button
                        onClick={handleClear}
                        disabled={isLoading || messages.length === 0}
                        size="icon"
                        variant="ghost"
                        className="h-9 w-9 rounded-full text-muted-foreground hover:text-red-500 hover:bg-red-500/10 shrink-0"
                        title="Clear history"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>

                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Ask anything..."
                        disabled={isLoading}
                        className="flex-1 bg-transparent border-none text-sm placeholder:text-muted-foreground/60 focus:ring-0 max-h-[120px] min-h-[36px] items-center py-2 resize-none overflow-y-auto scrollbar-hide"
                        style={{ height: '36px' }} // Initial height
                    />

                    <Button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        size="icon"
                        className={`h-9 w-9 rounded-full shrink-0 transition-all ${!input.trim() ? 'opacity-50' : 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-md'}`}
                    >
                        {isLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4 ml-0.5" />
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}
