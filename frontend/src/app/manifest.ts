import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
    return {
        name: 'ExamAI Pro',
        short_name: 'ExamAI Pro',
        description: 'AI-powered exam preparation platform',
        start_url: '/',
        display: 'fullscreen', // Use fullscreen to extend into Dynamic Island area
        background_color: '#1c1917', // Match dark theme background
        theme_color: '#000000',
        icons: [
            {
                src: '/globe.svg',
                sizes: 'any',
                type: 'image/svg+xml',
            },
        ],
    }
}
