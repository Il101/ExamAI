"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowRight, Sparkles, Zap, Shield } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden selection:bg-primary/30">
      {/* Background Gradients */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl opacity-50 animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-3xl opacity-50 animate-pulse delay-1000" />
      </div>

      {/* Navbar */}
      <nav className="container mx-auto px-6 py-6 flex items-center justify-between relative z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/80">
            ExamAI Pro
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login">
            <Button variant="ghost" className="text-muted-foreground hover:text-white">
              Log in
            </Button>
          </Link>
          <Link href="/register">
            <Button variant="glow" size="sm">
              Get Started
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 md:py-32 flex flex-col items-center text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm text-primary mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            AI-Powered Exam Prep
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white via-white/90 to-white/50">
            Master Your Exams <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-secondary">
              With Superhuman Speed
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 leading-relaxed">
            Stop wasting time on ineffective study methods. Our AI analyzes your learning style and creates a personalized path to success.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register">
              <Button size="lg" variant="glow" className="h-12 px-8 text-base">
                Start Learning Now <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </Link>
            <Link href="#features">
              <Button size="lg" variant="outline" className="h-12 px-8 text-base">
                Explore Features
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-6 py-24 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Zap className="w-6 h-6 text-yellow-400" />}
            title="Instant Feedback"
            description="Get real-time explanations for every answer. Understand the 'why' behind every question instantly."
            delay={0.2}
          />
          <FeatureCard
            icon={<Shield className="w-6 h-6 text-blue-400" />}
            title="Adaptive Learning"
            description="Our algorithm adapts to your weak points, ensuring you focus on what matters most for your exam."
            delay={0.4}
          />
          <FeatureCard
            icon={<Sparkles className="w-6 h-6 text-purple-400" />}
            title="Smart Analytics"
            description="Track your progress with beautiful, detailed analytics that show exactly how close you are to your goal."
            delay={0.6}
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description, delay }: { icon: React.ReactNode; title: string; description: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
    >
      <Card className="h-full border-white/5 bg-white/5 hover:bg-white/10 transition-colors">
        <CardHeader>
          <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center mb-4 border border-white/10">
            {icon}
          </div>
          <CardTitle className="text-xl text-white">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="text-base text-muted-foreground">
            {description}
          </CardDescription>
        </CardContent>
      </Card>
    </motion.div>
  );
}
