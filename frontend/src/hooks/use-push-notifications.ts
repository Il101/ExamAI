'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/client';
import { toast } from 'sonner';

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;

export function usePushNotifications() {
    const [permission, setPermission] = useState<NotificationPermission>('default');
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [subscription, setSubscription] = useState<PushSubscription | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if ('Notification' in window) {
            setPermission(Notification.permission);
        }

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.ready.then((registration) => {
                registration.pushManager.getSubscription().then((sub) => {
                    setSubscription(sub);
                    setIsSubscribed(!!sub);
                });
            });
        }
    }, []);

    const urlBase64ToUint8Array = (base64String: string) => {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    };

    const subscribe = useCallback(async () => {
        if (!VAPID_PUBLIC_KEY) {
            console.error('VAPID public key is not configured');
            toast.error('Push notifications are not configured on the server.');
            return;
        }

        try {
            setIsLoading(true);

            // 1. Request permission
            const status = await Notification.requestPermission();
            setPermission(status);

            if (status !== 'granted') {
                toast.error('Permission not granted for notifications');
                return;
            }

            // 2. Register/Get Service Worker
            const registration = await navigator.serviceWorker.register('/sw.js');
            await navigator.serviceWorker.ready;

            // 3. Subscribe to push manager
            const sub = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
            });

            // 4. Send subscription to backend
            const subJSON = sub.toJSON();
            await api.post('/push/subscribe', {
                endpoint: sub.endpoint,
                p256dh: subJSON.keys?.p256dh,
                auth: subJSON.keys?.auth
            });

            setSubscription(sub);
            setIsSubscribed(true);
            toast.success('Successfully subscribed to browser notifications!');
        } catch (error) {
            console.error('Failed to subscribe to push notifications:', error);
            toast.error('Failed to enable browser notifications.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const unsubscribe = useCallback(async () => {
        try {
            setIsLoading(true);
            if (subscription) {
                // 1. Get keys before unsubscribing
                const subJSON = subscription.toJSON();

                // 2. Unsubscribe from push manager
                await subscription.unsubscribe();

                // 3. Inform backend
                await api.post('/push/unsubscribe', {
                    endpoint: subscription.endpoint,
                    p256dh: subJSON.keys?.p256dh,
                    auth: subJSON.keys?.auth
                });
            }

            setSubscription(null);
            setIsSubscribed(false);
            toast.success('Unsubscribed from browser notifications.');
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
            toast.error('Failed to disable browser notifications.');
        } finally {
            setIsLoading(false);
        }
    }, [subscription]);

    return {
        permission,
        isSubscribed,
        subscribe,
        unsubscribe,
        isLoading
    };
}
