import React from 'react';
import './HomePage.css';
import PrescriptionPricePredictor from './PrescriptionPricePredictor';

export default function HomePage({ onGetStarted }) {
    return (
        <div className="home-container animate-fade-in">
            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-content">
                    <h1 className="hero-title animate-slide-down">
                        Smarter Healthcare <br />
                        <span className="teal-gradient-text">with AI-Powered Assistance</span>
                    </h1>
                    <p className="hero-subtitle animate-fade-up" style={{ animationDelay: '0.2s' }}>
                        MediRelease is an enterprise-grade platform streamlining medical documentation,
                        patient safety, and cost transparency with advanced AI-driven medical analysis.
                    </p>
                    <div className="hero-cta animate-fade-up" style={{ animationDelay: '0.4s' }}>
                        <button onClick={onGetStarted} className="btn-primary btn-primary-shimmer btn-lg hover-scale">
                            Get Started
                        </button>
                        <ul className="hero-highlights">
                            <li className="hover-glow">✨ Cost Reduction</li>
                            <li className="hover-glow">🛡️ Patient Safety</li>
                            <li className="hover-glow">🧠 AI Analysis</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Price Predictor Section */}
            <section className="predictor-outer-section animate-fade-up" style={{ animationDelay: '0.6s' }}>
                <div className="section-header">
                    <h2 className="teal-gradient-text">Generic Price Predictor</h2>
                    <p>Compare medicine prices across major online pharmacies instantly.</p>
                </div>
                <div className="card teal-glow">
                    <PrescriptionPricePredictor />
                </div>
            </section>

            {/* Features Section */}
            <section className="features-section">
                <div className="section-header animate-fade-in">
                    <h2>Advanced Features</h2>
                    <p>Empowering healthcare with state-of-the-art digital tools.</p>
                </div>
                <div className="features-grid staggered-list">
                    <div className="feature-card card hover-glow">
                        <div className="feature-icon animate-float">📄</div>
                        <h3 className="teal-gradient-text">AI Discharge Summary</h3>
                        <p>Automatically generate structured, clear, and professional discharge reports.</p>
                    </div>
                    <div className="feature-card card hover-glow">
                        <div className="feature-icon animate-float" style={{ animationDelay: '0.5s' }}>📈</div>
                        <h3 className="teal-gradient-text">Health Updates</h3>
                        <p>Real-time tracking of patient vitals and daily recovery logs.</p>
                    </div>
                    <div className="feature-card card hover-glow">
                        <div className="feature-icon animate-float" style={{ animationDelay: '1s' }}>💰</div>
                        <h3 className="teal-gradient-text">Cost Insights</h3>
                        <p>Transparency in medical billing with AI-driven savings analysis.</p>
                    </div>
                </div>
            </section>

            {/* Final CTA Section */}
            <section className="final-cta-section animate-fade-up">
                <div className="cta-card card teal-glow">
                    <h2 className="teal-gradient-text">Ready to experience the future?</h2>
                    <p>Join MediRelease today and transform how you manage healthcare.</p>
                    <button onClick={onGetStarted} className="btn-primary btn-primary-shimmer btn-lg hover-scale">
                        Access Dashboard Now
                    </button>
                </div>
            </section>

            <footer className="home-footer animate-fade-in">
                <p>&copy; 2026 MediRelease. Built for trust and efficiency.</p>
                <div className="footer-disclaimer">
                    <small>Disclaimer: This system provides decision support and does not replace medical authority.</small>
                </div>
            </footer>
        </div>
    );
}
