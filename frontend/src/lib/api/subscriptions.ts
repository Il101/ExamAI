import { api } from './client';

export interface PlanPrice {
    amount: number;
    currency: string;
}

export interface Plan {
    id: string;
    name: string;
    description?: string;
    price: {
        amount?: number;
        currency?: string;
        billing_period?: string | null;
        monthly?: PlanPrice;
        yearly?: PlanPrice;
    };
    limits?: {
        max_exams: number | null;
        max_topics_per_exam: number | null;
        daily_tutor_messages: number | null;
        max_simultaneous_sessions: number;
        max_team_members?: number;
    };
    features: {
        max_exams?: number | null;
        ai_model?: string;
        advanced_analytics?: boolean;
        export?: boolean;
        export_pdf?: boolean;
        priority_support?: boolean;
        priority_generation?: boolean;
        spaced_repetition?: boolean;
        ai_tutor?: boolean;
        team_management?: boolean;
    };
    lemonsqueezy_variant_id_monthly?: string;
    lemonsqueezy_variant_id_yearly?: string;
    popular?: boolean;
}

export interface Subscription {
    id: string;
    user_id: string;
    plan_type: string;
    status: string;
    current_period_start: string;
    current_period_end: string;
    external_subscription_id: string | null;
    customer_portal_url: string | null;
    cancel_at_period_end: boolean;
    canceled_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface UsageMetric {
    current: number;
    limit: number | null;
}

export interface UsageResponse {
    exams: UsageMetric;
    tutor_messages: UsageMetric;
    plan_id: string;
    status: string;
    current_period_end: string;
    customer_portal_url: string | null;
}

export interface CheckoutResponse {
    checkout_url: string;
}

export interface PortalResponse {
    portal_url: string;
}

export const subscriptionsApi = {
    getPlans: async (): Promise<Plan[]> => {
        const response = await api.get<Plan[]>('/subscriptions/plans');
        return response.data;
    },

    getCurrentSubscription: async (): Promise<Subscription> => {
        const response = await api.get<Subscription>('/subscriptions/current');
        return response.data;
    },

    createCheckout: async (
        planId: string,
        successUrl: string,
        cancelUrl: string,
        billingPeriod?: 'monthly' | 'yearly'
    ): Promise<CheckoutResponse> => {
        const response = await api.post<CheckoutResponse>('/subscriptions/checkout', {
            plan_id: planId,
            success_url: successUrl,
            cancel_url: cancelUrl,
            billing_period: billingPeriod || 'monthly',
        });
        return response.data;
    },

    cancelSubscription: async (): Promise<Subscription> => {
        const response = await api.post<Subscription>('/subscriptions/cancel');
        return response.data;
    },

    reactivateSubscription: async (): Promise<Subscription> => {
        const response = await api.post<Subscription>('/subscriptions/reactivate');
        return response.data;
    },

    getPortalLink: async (): Promise<PortalResponse> => {
        const response = await api.post<PortalResponse>('/subscriptions/portal');
        return response.data;
    },

    getUsage: async (): Promise<UsageResponse> => {
        const response = await api.get<UsageResponse>('/subscriptions/usage');
        return response.data;
    },
};
