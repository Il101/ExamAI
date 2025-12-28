'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface NavItem {
    name: string;
    href: string;
    icon?: any;
    completed?: boolean;
    id?: string;
}

interface ContextualNav {
    title: string;
    items: NavItem[];
    progress?: number;
}

interface SidebarContextType {
    isCollapsed: boolean;
    setIsCollapsed: (collapsed: boolean) => void;
    toggleCollapsed: () => void;
    contextualNav: ContextualNav | null;
    setContextualNav: (nav: ContextualNav | null) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export function SidebarProvider({ children }: { children: ReactNode }) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [contextualNav, setContextualNav] = useState<ContextualNav | null>(null);

    const toggleCollapsed = () => {
        setIsCollapsed(prev => !prev);
    };

    return (
        <SidebarContext.Provider value={{
            isCollapsed,
            setIsCollapsed,
            toggleCollapsed,
            contextualNav,
            setContextualNav
        }}>
            {children}
        </SidebarContext.Provider>
    );
}

export function useSidebar() {
    const context = useContext(SidebarContext);
    if (context === undefined) {
        throw new Error('useSidebar must be used within a SidebarProvider');
    }
    return context;
}
