import ParticleBackground from "@/components/ParticleBackground";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Privacy() {
    return (
        <div className="min-h-screen bg-background relative overflow-hidden">
            <ParticleBackground />
            <div className="container mx-auto px-6 py-20 relative z-10">
                <div className="max-w-3xl mx-auto">
                    <Link href="/">
                        <Button variant="ghost" className="mb-8 pl-0 hover:bg-transparent hover:text-primary transition-colors">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back to Home
                        </Button>
                    </Link>

                    <h1 className="text-4xl font-bold mb-12 bg-gradient-brand bg-clip-text text-transparent inline-block">
                        Datenschutzerklärung (Privacy Policy)
                    </h1>

                    <div className="space-y-8 text-foreground">
                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">1. Verantwortlicher (Controller)</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Ilia Zharikov<br />
                                Österreich, Hall in Tirol, Salvatorgasse 2a/18.<br />
                                E-Mail: iljarikov@gmail.com
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">2. Hosting & Backend</h2>
                            <p className="text-muted-foreground leading-relaxed mb-4">
                                Wir nutzen externe Dienstleister für das Hosting unserer Datenbanken und Anwendungen. Diese Anbieter verarbeiten Daten in unserem Auftrag (Auftragsverarbeiter):
                            </p>
                            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                <li><strong className="text-foreground">Vercel Inc.</strong> (USA) – Frontend Hosting.</li>
                                <li><strong className="text-foreground">Railway Corp.</strong> (USA) – Backend Hosting & Analytics.</li>
                                <li><strong className="text-foreground">Supabase Inc.</strong> (USA/EU) – Datenbank & Authentifizierung.</li>
                            </ul>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">3. KI-Generierung (Google Gemini)</h2>
                            <p className="text-muted-foreground leading-relaxed mb-4">
                                Zur Erstellung von Zusammenfassungen und Tests nutzen wir die API von <strong className="text-foreground">Google (Gemini)</strong>.
                            </p>
                            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                <li>Ihre hochgeladenen Dokumente (PDF/Texte) werden zur Verarbeitung an Google-Server gesendet.</li>
                                <li>Google nutzt diese Daten gemäß eigenen Datenschutzbestimmungen zur Bereitstellung des Dienstes.</li>
                                <li className="text-destructive/80 font-medium">Wichtig: Laden Sie keine vertraulichen persönlichen Daten (Gesundheitsdaten, Finanzdaten) in die Dokumente hoch.</li>
                            </ul>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">4. Zahlungen (Stripe)</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Die Zahlungsabwicklung erfolgt über <strong className="text-foreground">Stripe Payments Europe, Ltd.</strong> Wir speichern keine Kreditkartendaten. Stripe verarbeitet diese Daten als eigener Verantwortlicher.
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">5. Speicherdauer</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Ihre hochgeladenen Dateien bleiben in unserer Datenbank gespeichert, solange Ihr Konto aktiv ist, damit Sie jederzeit darauf zugreifen können. Sie können einzelne Dateien oder Ihr gesamtes Konto jederzeit löschen.
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">6. Ihre Rechte</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Sie haben das Recht auf Auskunft, Berichtigung und Löschung Ihrer Daten. Kontaktieren Sie uns unter <a href="mailto:iljarikov@gmail.com" className="text-primary hover:underline">iljarikov@gmail.com</a>.
                            </p>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
}
