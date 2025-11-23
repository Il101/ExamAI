"use client";

import { useState, useRef } from "react";
import { Upload, Brain, Zap, Target, BookOpen, Briefcase, Sparkles, CheckCircle2, ArrowRight, Clock, TrendingUp, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useScrollAnimation } from "@/lib/hooks/useScrollAnimation";
import ParticleBackground from "@/components/ParticleBackground";
import AnimatedCounter from "@/components/AnimatedCounter";
import LearningProcessAnimation from "@/components/LearningProcessAnimation";
import TopicOutline from "@/components/TopicOutline";
import { analyzeApi, TopicOutline as TopicOutlineType } from "@/lib/api/analyze";
import { toast } from "sonner";
import Link from "next/link";

export default function Index() {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [outline, setOutline] = useState<TopicOutlineType | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const problemSolution = useScrollAnimation();
  const scienceEngine = useScrollAnimation();
  const useCases = useScrollAnimation();
  const howItWorks = useScrollAnimation();
  const stats = useScrollAnimation();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await processFile(files[0]);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await processFile(files[0]);
    }
  };

  const processFile = async (file: File) => {
    // Validate file size (10MB)
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      toast.error("File too large. Maximum size is 10MB.");
      return;
    }

    // Validate file type
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ];

    if (!allowedTypes.includes(file.type)) {
      toast.error("Unsupported file type. Please upload PDF, DOCX, or TXT files.");
      return;
    }

    setIsProcessing(true);
    setLogs([]);
    setOutline(null);

    const logMessages = [
      "🔍 Analyzing document structure...",
      "🧠 Extracting topics and concepts...",
      "📊 Building knowledge hierarchy...",
      "✨ Creating learning outline...",
    ];

    // Show logs progressively
    logMessages.forEach((msg, index) => {
      setTimeout(() => {
        setLogs(prev => [...prev, msg]);
      }, index * 600);
    });

    try {
      const result = await analyzeApi.analyzeContent(file);

      setTimeout(() => {
        setLogs(prev => [...prev, "✅ Analysis complete!"]);
        setTimeout(() => {
          setOutline(result);
          setIsProcessing(false);

          // Store in localStorage for potential use after registration
          localStorage.setItem('lastAnalyzedOutline', JSON.stringify(result));
        }, 500);
      }, logMessages.length * 600);

    } catch (error) {
      console.error("Analysis error:", error);
      setIsProcessing(false);
      toast.error("Failed to analyze file. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Hero Section */}
      <section className="relative overflow-hidden min-h-screen flex items-center">
        <ParticleBackground />
        <div className="absolute inset-0 bg-gradient-glow opacity-50" />

        {/* Learning Process Animation Background */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <LearningProcessAnimation />
        </div>

        <div className="container mx-auto px-6 py-20 relative">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/50 backdrop-blur-sm mb-8 animate-fade-in glow-pulse">
              <Sparkles className="w-4 h-4 text-primary floating" />
              <span className="text-sm font-medium text-accent-foreground">Powered by Gemini 2.0 Flash</span>
            </div>

            <h1 className="text-5xl md:text-7xl font-bold mb-6 text-foreground animate-fade-in-up">
              Turn any file into a{" "}
              <span className="bg-gradient-brand bg-clip-text text-transparent">
                personalized course
              </span>
              {" "}in 30 seconds
            </h1>

            <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
              AI agent creates structure, tests, and spaced repetition plan.
              Learning designed for your brain&apos;s architecture.
            </p>

            {/* Interactive Upload Zone */}
            <div
              className={`max-w-2xl mx-auto transition-all duration-300 animate-scale-in hover-lift ${isDragging ? "scale-105" : ""}`}
              style={{ animationDelay: "0.2s" }}
            >
              <Card
                className={`border-2 border-dashed transition-all duration-300 ${isDragging
                  ? "border-primary bg-accent shadow-glow"
                  : "border-border bg-card hover:border-primary/50 hover:shadow-large"
                  }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <CardContent className="p-12">
                  {!outline && !isProcessing && (
                    <div className="text-center space-y-4">
                      <div className="inline-flex p-4 rounded-full bg-gradient-brand mb-4 floating">
                        <Upload className="w-8 h-8 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-lg font-semibold text-foreground mb-2">
                          Drag file here
                        </p>
                        <p className="text-sm text-muted-foreground mb-4">
                          PDF, DOCX, TXT — up to 10 MB
                        </p>
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileInputChange}
                        className="hidden"
                      />
                      <Button
                        size="lg"
                        className="bg-gradient-brand hover:opacity-90 transition-all hover:scale-105 hover:shadow-glow"
                        onClick={handleFileSelect}
                      >
                        Or select file
                      </Button>
                    </div>
                  )}

                  {isProcessing && (
                    <div className="space-y-3 font-mono text-sm">
                      {logs.map((log, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 animate-fade-in"
                        >
                          <span className="text-success">→</span>
                          <span className="text-foreground">{log}</span>
                        </div>
                      ))}
                      <div className="flex items-center gap-2">
                        <span className="text-success">→</span>
                        <span className="text-foreground">Processing</span>
                        <span className="animate-blink">_</span>
                      </div>
                    </div>
                  )}

                  {outline && !isProcessing && (
                    <div className="space-y-6">
                      <TopicOutline outline={outline} />

                      <div className="flex justify-center pt-4">
                        <Link href="/register">
                          <Button
                            size="lg"
                            className="bg-gradient-brand hover:opacity-90 transition-all hover:scale-105 hover:shadow-glow"
                          >
                            Start Learning
                            <ArrowRight className="ml-2 w-5 h-5" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              <p className="text-xs text-muted-foreground mt-4 flex items-center justify-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-success" />
                Safe and anonymous
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section ref={stats.ref} className="py-20 bg-background relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary rounded-full blur-3xl floating" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary rounded-full blur-3xl floating-delayed" />
        </div>

        <div className="container mx-auto px-6 relative">
          <div className="grid md:grid-cols-2 gap-16 max-w-4xl mx-auto">
            <div className={`text-center space-y-4 scroll-reveal ${stats.isVisible ? "visible" : ""}`}>
              <div className="flex items-center justify-center gap-3">
                <Clock className="w-8 h-8 text-secondary" />
                <div className="text-6xl md:text-7xl font-bold text-foreground">
                  90<span className="text-secondary">%</span>
                </div>
              </div>
              <div className="flex items-center justify-center gap-2">
                <p className="text-muted-foreground text-lg">Retention rate</p>
                <div className="group relative">
                  <HelpCircle className="w-4 h-4 text-muted-foreground cursor-help" />
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 p-3 bg-card border border-border rounded-lg shadow-lg text-sm text-foreground z-10">
                    <p className="font-semibold mb-1">What is retention rate?</p>
                    <p className="text-muted-foreground">The percentage of information you remember after learning with our AI-powered system</p>
                  </div>
                </div>
              </div>
            </div>

            <div className={`text-center space-y-4 scroll-reveal ${stats.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.1s" }}>
              <div className="flex items-center justify-center gap-3">
                <TrendingUp className="w-8 h-8 text-success" />
                <div className="text-6xl md:text-7xl font-bold text-foreground">
                  10<span className="text-success">x</span>
                </div>
              </div>
              <p className="text-muted-foreground text-lg">Faster learning</p>
            </div>
          </div>
        </div>
      </section>

      {/* Problem vs Solution */}
      <section ref={problemSolution.ref} className="py-24 bg-background relative">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Pain */}
            <Card className={`border-2 border-destructive/20 bg-card/50 backdrop-blur hover-lift scroll-reveal ${problemSolution.isVisible ? "visible" : ""}`}>
              <CardContent className="p-8 space-y-4">
                <div className="inline-flex p-3 rounded-lg bg-destructive/10">
                  <Target className="w-6 h-6 text-destructive" />
                </div>
                <h3 className="text-2xl font-bold text-foreground">Cramming Method</h3>
                <div className="space-y-3 text-muted-foreground">
                  <p>📚 3 hours of reading</p>
                  <p>😰 Chaos and information overload</p>
                  <p>📉 10% retention after a week</p>
                  <p>🔄 Endless re-reading</p>
                </div>
              </CardContent>
            </Card>

            {/* Solution */}
            <Card className={`border-2 border-primary shadow-glow bg-card hover-lift scroll-reveal ${problemSolution.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.2s" }}>
              <CardContent className="p-8 space-y-4">
                <div className="inline-flex p-3 rounded-lg bg-gradient-brand floating">
                  <Zap className="w-6 h-6 text-primary-foreground" />
                </div>
                <h3 className="text-2xl font-bold text-foreground">Neuro-Learning</h3>
                <div className="space-y-3 text-foreground">
                  <p>⚡ 30 minutes of focus</p>
                  <p>🎯 Structured learning</p>
                  <p>📈 90% retention</p>
                  <p>🧠 Active Recall instead of passive reading</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* The Science Engine */}
      <section ref={scienceEngine.ref} className="py-24 bg-background relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-brand animate-gradient" />
        </div>

        <div className="container mx-auto px-6 relative">
          <div className="max-w-6xl mx-auto">
            <div className={`text-center mb-16 scroll-reveal ${scienceEngine.isVisible ? "visible" : ""}`}>
              <h2 className="text-4xl md:text-5xl font-bold mb-4 text-foreground">
                Hacking your brain&apos;s{" "}
                <span className="bg-gradient-brand bg-clip-text text-transparent">
                  biology with code
                </span>
              </h2>
              <p className="text-xl text-muted-foreground">
                Science wrapped in Magic
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {/* Card 1 */}
              <Card className={`group hover-lift bg-card scroll-reveal ${scienceEngine.isVisible ? "visible" : ""}`}>
                <CardContent className="p-8 space-y-4">
                  <div className="inline-flex p-3 rounded-lg bg-primary/10 group-hover:bg-gradient-brand transition-all duration-300 floating">
                    <Brain className="w-8 h-8 text-primary group-hover:text-primary-foreground transition-colors" />
                  </div>
                  <h3 className="text-xl font-bold text-foreground">
                    Neural Reinforcement Engine
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    <span className="font-semibold text-foreground">Smart Decay Algorithms.</span> Our AI calculates
                    memory &quot;half-life&quot; and activates neural connections right at the moment of forgetting.
                  </p>
                </CardContent>
              </Card>

              {/* Card 2 */}
              <Card className={`group hover-lift bg-card scroll-reveal ${scienceEngine.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.1s" }}>
                <CardContent className="p-8 space-y-4">
                  <div className="inline-flex p-3 rounded-lg bg-secondary/10 group-hover:bg-gradient-brand transition-all duration-300 floating-delayed">
                    <Zap className="w-8 h-8 text-secondary group-hover:text-primary-foreground transition-colors" />
                  </div>
                  <h3 className="text-xl font-bold text-foreground">
                    Active Retrieval Core
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    <span className="font-semibold text-foreground">Stop Re-reading.</span> Passive reading is an illusion.
                    AI generates contextual questions, forcing your brain to <em>retrieve</em> information, strengthening synapses.
                  </p>
                </CardContent>
              </Card>

              {/* Card 3 */}
              <Card className={`group hover-lift bg-card scroll-reveal ${scienceEngine.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.2s" }}>
                <CardContent className="p-8 space-y-4">
                  <div className="inline-flex p-3 rounded-lg bg-success/10 group-hover:bg-gradient-brand transition-all duration-300 floating">
                    <Target className="w-8 h-8 text-success group-hover:text-primary-foreground transition-colors" />
                  </div>
                  <h3 className="text-xl font-bold text-foreground">
                    Cognitive Load Balancer
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    <span className="font-semibold text-foreground">No Information Overload.</span> AI breaks complex
                    lectures into atomic concepts, perfectly sized for your working memory.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section ref={useCases.ref} className="py-24 bg-background">
        <div className="container mx-auto px-6">
          <div className="max-w-6xl mx-auto">
            <div className={`text-center mb-16 scroll-reveal ${useCases.isVisible ? "visible" : ""}`}>
              <h2 className="text-4xl md:text-5xl font-bold mb-4 text-foreground">
                Universal learning for everyone
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Students */}
              <div className={`text-center space-y-4 hover-lift scroll-reveal ${useCases.isVisible ? "visible" : ""}`}>
                <div className="inline-flex p-4 rounded-full bg-gradient-brand mb-4 floating">
                  <BookOpen className="w-8 h-8 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-bold text-foreground">Students</h3>
                <p className="text-muted-foreground">
                  Pass exams without sleepless nights. Upload 500 pages of textbook — get the essence.
                </p>
                <p className="text-sm text-accent-foreground font-medium">Med • Law • Engineering</p>
              </div>

              {/* Professionals */}
              <div className={`text-center space-y-4 hover-lift scroll-reveal ${useCases.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.1s" }}>
                <div className="inline-flex p-4 rounded-full bg-gradient-brand mb-4 floating-delayed">
                  <Briefcase className="w-8 h-8 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-bold text-foreground">Professionals</h3>
                <p className="text-muted-foreground">
                  Master new regulations or technology over the weekend. Fast onboarding to new topics.
                </p>
                <p className="text-sm text-accent-foreground font-medium">IT • Business • Finance</p>
              </div>

              {/* Self-Learners */}
              <div className={`text-center space-y-4 hover-lift scroll-reveal ${useCases.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.2s" }}>
                <div className="inline-flex p-4 rounded-full bg-gradient-brand mb-4 floating">
                  <Sparkles className="w-8 h-8 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-bold text-foreground">Self-Learners</h3>
                <p className="text-muted-foreground">
                  Study history or physics for yourself. Turn hobbies into systematic knowledge.
                </p>
                <p className="text-sm text-accent-foreground font-medium">Polymaths • Curious Minds</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section ref={howItWorks.ref} className="py-24 bg-background relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-primary rounded-full blur-3xl floating" />
        </div>

        <div className="container mx-auto px-6 relative">
          <div className="max-w-4xl mx-auto">
            <div className={`text-center mb-16 scroll-reveal ${howItWorks.isVisible ? "visible" : ""}`}>
              <h2 className="text-4xl md:text-5xl font-bold mb-4 text-foreground">
                Magic under the hood
              </h2>
              <p className="text-xl text-muted-foreground">
                Plan-and-Execute Architecture
              </p>
            </div>

            <div className="space-y-8">
              {/* Step 1 */}
              <div className={`flex gap-6 items-start scroll-reveal ${howItWorks.isVisible ? "visible" : ""}`}>
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-brand flex items-center justify-center text-primary-foreground font-bold shadow-glow">
                  1
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-foreground mb-2">Upload</h3>
                  <p className="text-muted-foreground">
                    You upload content (PDF, Video, Audio). All popular formats supported.
                  </p>
                </div>
              </div>

              {/* Step 2 */}
              <div className={`flex gap-6 items-start scroll-reveal ${howItWorks.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.1s" }}>
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-brand flex items-center justify-center text-primary-foreground font-bold shadow-glow">
                  2
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-foreground mb-2">Agent Planning</h3>
                  <p className="text-muted-foreground">
                    AI methodologist analyzes structure and builds knowledge graph.
                    Identifies key concepts and connections between them.
                  </p>
                </div>
              </div>

              {/* Step 3 */}
              <div className={`flex gap-6 items-start scroll-reveal ${howItWorks.isVisible ? "visible" : ""}`} style={{ transitionDelay: "0.2s" }}>
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-brand flex items-center justify-center text-primary-foreground font-bold shadow-glow">
                  3
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-foreground mb-2">Execution</h3>
                  <p className="text-muted-foreground">
                    Generation of personalized content, adaptive tests and learning schedule
                    based on your learning pace.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 bg-gradient-glow relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-brand opacity-5 animate-gradient bg-[length:200%_200%]" />
        <ParticleBackground />

        <div className="container mx-auto px-6 relative">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <h2 className="text-4xl md:text-6xl font-bold text-foreground animate-fade-in-up">
              Ready to learn{" "}
              <span className="bg-gradient-brand bg-clip-text text-transparent">
                10x faster
              </span>
              ?
            </h2>

            <p className="text-xl text-muted-foreground animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
              Focus on understanding, let AI handle the organizing.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-scale-in" style={{ animationDelay: "0.2s" }}>
              <Link href="/register">
                <Button
                  size="lg"
                  className="bg-gradient-brand hover:opacity-90 hover:scale-105 transition-all text-lg px-8 py-6 shadow-glow"
                >
                  Create first course for free
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 text-success" />
              No card required • Cancel anytime
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-border bg-muted/30 backdrop-blur">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-center md:text-left">
              <p className="text-2xl font-bold bg-gradient-brand bg-clip-text text-transparent">
                ExamAI Pro
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Don&apos;t just read. Absorb.
              </p>
            </div>

            <div className="flex gap-8 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors hover:scale-110 inline-block">About</a>
              <a href="#" className="hover:text-foreground transition-colors hover:scale-110 inline-block">Blog</a>
              <a href="#" className="hover:text-foreground transition-colors hover:scale-110 inline-block">Support</a>
              <a href="#" className="hover:text-foreground transition-colors hover:scale-110 inline-block">Privacy</a>
            </div>
          </div>

          <div className="text-center text-xs text-muted-foreground mt-8">
            © 2025 ExamAI Pro. Powered by Gemini 2.0 Flash.
          </div>
        </div>
      </footer>
    </div>
  );
}
