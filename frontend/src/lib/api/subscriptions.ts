import { api } from './client';

export interface Plan {
    id: string;
    name: string;
    price: {
        amount: number;
        currency: string;
        billing_period: string | null;
    };
    features: {
        max_exams: number | null;
        ai_model: string;
        advanced_analytics: boolean;
        export: boolean;
        priority_support: boolean;
    };
    stripe_price_id?: string;
    popular?: boolean;
}

export interface Subscription {
    id: string;
    user_id: string;
    plan_type: string;
    status: string;
    current_period_start: string;
    current_period_end: string;
    stripe_subscription_id: string | null;
    stripe_customer_id: string | null;
    cancel_at_period_end: boolean;
    canceled_at: string | null;
    created_at: string;
    updated_at: string;
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
        cancelUrl: string
    ): Promise<CheckoutResponse> => {
        const response = await api.post<CheckoutResponse>('/subscriptions/checkout', {
            plan_id: planId,
            success_url: successUrl,
            cancel_url: cancelUrl,
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
};
