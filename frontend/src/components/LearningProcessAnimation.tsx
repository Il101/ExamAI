"use client";

import { useEffect, useState } from "react";

const LearningProcessAnimation = () => {
    const [activeStep, setActiveStep] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setActiveStep((prev) => (prev + 1) % 4);
        }, 2000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="relative w-full max-w-2xl mx-auto h-[400px] opacity-20">
            <svg
                viewBox="0 0 800 400"
                className="w-full h-full"
                xmlns="http://www.w3.org/2000/svg"
            >
                <defs>
                    {/* Gradients */}
                    <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="hsl(238, 56%, 58%)" />
                        <stop offset="100%" stopColor="hsl(271, 81%, 56%)" />
                    </linearGradient>

                    <linearGradient id="dataFlow" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="hsl(238, 56%, 58%)" stopOpacity="0" />
                        <stop offset="50%" stopColor="hsl(238, 56%, 58%)" stopOpacity="1" />
                        <stop offset="100%" stopColor="hsl(238, 56%, 58%)" stopOpacity="0" />
                    </linearGradient>

                    {/* Glow filter */}
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>

                    {/* Patterns */}
                    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="hsl(238, 56%, 58%)" strokeWidth="0.5" opacity="0.1" />
                    </pattern>
                </defs>

                {/* Background Grid */}
                <rect width="800" height="400" fill="url(#grid)" />

                {/* Document Icon (Left) */}
                <g className={`transition-all duration-500 ${activeStep >= 0 ? 'opacity-100' : 'opacity-30'}`}>
                    <rect
                        x="50"
                        y="150"
                        width="120"
                        height="160"
                        rx="8"
                        fill="none"
                        stroke="url(#brainGradient)"
                        strokeWidth="3"
                        filter="url(#glow)"
                    >
                        <animate
                            attributeName="stroke-width"
                            values="3;5;3"
                            dur="2s"
                            repeatCount="indefinite"
                        />
                    </rect>

                    {/* Document lines */}
                    <line x1="70" y1="180" x2="150" y2="180" stroke="hsl(238, 56%, 58%)" strokeWidth="2" opacity="0.6">
                        <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" repeatCount="indefinite" />
                    </line>
                    <line x1="70" y1="200" x2="150" y2="200" stroke="hsl(238, 56%, 58%)" strokeWidth="2" opacity="0.6">
                        <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" begin="0.2s" repeatCount="indefinite" />
                    </line>
                    <line x1="70" y1="220" x2="130" y2="220" stroke="hsl(238, 56%, 58%)" strokeWidth="2" opacity="0.6">
                        <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" begin="0.4s" repeatCount="indefinite" />
                    </line>
                    <line x1="70" y1="240" x2="150" y2="240" stroke="hsl(238, 56%, 58%)" strokeWidth="2" opacity="0.6">
                        <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" begin="0.6s" repeatCount="indefinite" />
                    </line>
                    <line x1="70" y1="260" x2="140" y2="260" stroke="hsl(238, 56%, 58%)" strokeWidth="2" opacity="0.6">
                        <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" begin="0.8s" repeatCount="indefinite" />
                    </line>
                </g>

                {/* Data Flow Particles (Left to Center) */}
                <g className={`transition-opacity duration-500 ${activeStep >= 1 ? 'opacity-100' : 'opacity-0'}`}>
                    {[...Array(5)].map((_, i) => (
                        <circle
                            key={`particle-left-${i}`}
                            r="3"
                            fill="url(#brainGradient)"
                            filter="url(#glow)"
                        >
                            <animateMotion
                                dur="2s"
                                repeatCount="indefinite"
                                begin={`${i * 0.4}s`}
                                path="M 170 230 Q 280 180 350 200"
                            />
                            <animate
                                attributeName="opacity"
                                values="0;1;1;0"
                                dur="2s"
                                repeatCount="indefinite"
                                begin={`${i * 0.4}s`}
                            />
                        </circle>
                    ))}
                </g>

                {/* Processing Center (AI Agent) */}
                <g className={`transition-all duration-500 ${activeStep >= 2 ? 'opacity-100 scale-100' : 'opacity-30 scale-90'}`} transform-origin="400 200">
                    {/* Center hexagon */}
                    <path
                        d="M 400 150 L 440 175 L 440 225 L 400 250 L 360 225 L 360 175 Z"
                        fill="none"
                        stroke="url(#brainGradient)"
                        strokeWidth="3"
                        filter="url(#glow)"
                    >
                        <animateTransform
                            attributeName="transform"
                            attributeType="XML"
                            type="rotate"
                            from="0 400 200"
                            to="360 400 200"
                            dur="8s"
                            repeatCount="indefinite"
                        />
                    </path>

                    {/* Inner circles */}
                    <circle cx="400" cy="200" r="15" fill="url(#brainGradient)" opacity="0.8">
                        <animate attributeName="r" values="15;20;15" dur="2s" repeatCount="indefinite" />
                    </circle>

                    {/* Orbiting dots */}
                    {[0, 120, 240].map((angle, i) => (
                        <circle
                            key={`orbit-${i}`}
                            r="4"
                            fill="hsl(271, 81%, 56%)"
                            filter="url(#glow)"
                        >
                            <animateMotion
                                dur="3s"
                                repeatCount="indefinite"
                                path={`M ${400 + 30 * Math.cos((angle * Math.PI) / 180)} ${200 + 30 * Math.sin((angle * Math.PI) / 180)} 
                       A 30 30 0 1 1 ${400 + 30 * Math.cos(((angle + 359) * Math.PI) / 180)} ${200 + 30 * Math.sin(((angle + 359) * Math.PI) / 180)}`}
                            />
                        </circle>
                    ))}
                </g>

                {/* Data Flow Particles (Center to Right) */}
                <g className={`transition-opacity duration-500 ${activeStep >= 3 ? 'opacity-100' : 'opacity-0'}`}>
                    {[...Array(5)].map((_, i) => (
                        <circle
                            key={`particle-right-${i}`}
                            r="3"
                            fill="url(#brainGradient)"
                            filter="url(#glow)"
                        >
                            <animateMotion
                                dur="2s"
                                repeatCount="indefinite"
                                begin={`${i * 0.4}s`}
                                path="M 450 200 Q 560 220 630 200"
                            />
                            <animate
                                attributeName="opacity"
                                values="0;1;1;0"
                                dur="2s"
                                repeatCount="indefinite"
                                begin={`${i * 0.4}s`}
                            />
                        </circle>
                    ))}
                </g>

                {/* Brain/Knowledge Icon (Right) */}
                <g className={`transition-all duration-500 ${activeStep >= 3 ? 'opacity-100' : 'opacity-30'}`}>
                    {/* Brain outline */}
                    <path
                        d="M 680 180 Q 720 160 730 200 Q 740 180 750 200 Q 750 240 730 240 Q 720 260 680 240 Q 640 260 650 200 Q 660 180 680 180 Z"
                        fill="none"
                        stroke="url(#brainGradient)"
                        strokeWidth="3"
                        filter="url(#glow)"
                    >
                        <animate
                            attributeName="stroke-width"
                            values="3;4;3"
                            dur="2s"
                            repeatCount="indefinite"
                        />
                    </path>

                    {/* Neural network inside brain */}
                    <g opacity="0.8">
                        <circle cx="680" cy="200" r="3" fill="hsl(238, 56%, 58%)">
                            <animate attributeName="r" values="3;5;3" dur="1.5s" repeatCount="indefinite" />
                        </circle>
                        <circle cx="700" cy="190" r="3" fill="hsl(238, 56%, 58%)">
                            <animate attributeName="r" values="3;5;3" dur="1.5s" begin="0.3s" repeatCount="indefinite" />
                        </circle>
                        <circle cx="700" cy="210" r="3" fill="hsl(238, 56%, 58%)">
                            <animate attributeName="r" values="3;5;3" dur="1.5s" begin="0.6s" repeatCount="indefinite" />
                        </circle>
                        <circle cx="720" cy="200" r="3" fill="hsl(238, 56%, 58%)">
                            <animate attributeName="r" values="3;5;3" dur="1.5s" begin="0.9s" repeatCount="indefinite" />
                        </circle>

                        <line x1="680" y1="200" x2="700" y2="190" stroke="hsl(238, 56%, 58%)" strokeWidth="1">
                            <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite" />
                        </line>
                        <line x1="680" y1="200" x2="700" y2="210" stroke="hsl(238, 56%, 58%)" strokeWidth="1">
                            <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" begin="0.3s" repeatCount="indefinite" />
                        </line>
                        <line x1="700" y1="190" x2="720" y2="200" stroke="hsl(238, 56%, 58%)" strokeWidth="1">
                            <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" begin="0.6s" repeatCount="indefinite" />
                        </line>
                        <line x1="700" y1="210" x2="720" y2="200" stroke="hsl(238, 56%, 58%)" strokeWidth="1">
                            <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" begin="0.9s" repeatCount="indefinite" />
                        </line>
                    </g>

                    {/* Success stars */}
                    {[0, 1, 2].map((i) => (
                        <g key={`star-${i}`} opacity="0.6">
                            <path
                                d={`M ${680 + i * 20} ${160 + i * 5} l 3 3 l -3 3 l 3 3 l -3 3 l -3 -3 l -3 3 l -3 -3 l 3 -3 l -3 -3 Z`}
                                fill="hsl(142, 71%, 45%)"
                                filter="url(#glow)"
                            >
                                <animate
                                    attributeName="opacity"
                                    values="0;1;0"
                                    dur="3s"
                                    begin={`${i * 0.5}s`}
                                    repeatCount="indefinite"
                                />
                                <animateTransform
                                    attributeName="transform"
                                    type="scale"
                                    values="0;1.5;0"
                                    dur="3s"
                                    begin={`${i * 0.5}s`}
                                    repeatCount="indefinite"
                                    additive="sum"
                                />
                            </path>
                        </g>
                    ))}
                </g>

                {/* Labels */}
                <text x="110" y="330" textAnchor="middle" fill="hsl(238, 56%, 58%)" fontSize="14" fontWeight="600" opacity="0.8">
                    Upload
                </text>
                <text x="400" y="280" textAnchor="middle" fill="hsl(238, 56%, 58%)" fontSize="14" fontWeight="600" opacity="0.8">
                    AI Processing
                </text>
                <text x="700" y="280" textAnchor="middle" fill="hsl(142, 71%, 45%)" fontSize="14" fontWeight="600" opacity="0.8">
                    Knowledge
                </text>
            </svg>
        </div>
    );
};

export default LearningProcessAnimation;
