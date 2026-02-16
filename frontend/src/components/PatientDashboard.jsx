import { useState, useEffect } from 'react';
import {
    downloadDischargeSummaryPDF
} from '../utils/api';
import './PatientDashboard.css';

export default function PatientDashboard({ onLogout }) {
    const [activeTab, setActiveTab] = useState('billing');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [billingData, setBillingData] = useState({
        estimated_total: 0,
        duration_days: 0,
        breakdown: []
    });
    const [billAnalysis, setBillAnalysis] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [dischargeSummary, setDischargeSummary] = useState(null);

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const patientId = user.userId;

    useEffect(() => {
        loadBillingData();
        loadTimeline();
        loadDischargeSummary();
    }, [patientId]);

    const loadBillingData = async () => {
        try {
            const res = await fetch(`http://localhost:8002/api/patient/cost-summary?patient_id=${patientId}`);
            if (res.ok) {
                const data = await res.json();
                setBillingData({
                    estimated_total: data.estimated_total,
                    duration_days: data.visit_count || 0,
                    breakdown: data.breakdown.map(item => ({ category: item.item, cost: item.total }))
                });
            }
        } catch (err) {
            console.error('Error loading billing data:', err);
        }
    };

    const loadTimeline = async () => {
        try {
            const res = await fetch(`http://localhost:8002/api/patient/timeline?patient_id=${patientId}`);
            if (res.ok) {
                const data = await res.json();
                setTimeline(data);
            }
        } catch (err) {
            console.error('Error loading timeline:', err);
        }
    };

    const loadDischargeSummary = async () => {
        try {
            const res = await fetch(`http://localhost:8002/api/patient/discharge-summaries?patient_id=${patientId}`);
            if (res.ok) {
                const summaries = await res.json();
                if (summaries.length > 0) {
                    setDischargeSummary(summaries[0]);
                }
            }
        } catch (err) {
            console.error('Error loading discharge summary:', err);
        }
    };

    const handleDownloadPDF = async () => {
        if (!dischargeSummary) return;
        setLoading(true);
        try {
            const blob = await downloadDischargeSummaryPDF(dischargeSummary.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `discharge_summary_${dischargeSummary.id}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
            setSuccess('PDF downloaded successfully!');
        } catch (err) {
            setError('Failed to download PDF');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="dashboard-container animate-fade-in">
            <header className="dashboard-header">
                <h1 className="teal-gradient-text animate-slide-down">MediRelease patient portal</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <span className="user-welcome">Welcome, {user.username}</span>
                    <button onClick={onLogout} className="logout-btn hover-scale">Logout</button>
                </div>
            </header>

            <div className="tabs-nav animate-slide-down" style={{ animationDelay: '0.1s' }}>
                <button
                    className={`hover-glow ${activeTab === 'billing' ? 'active' : ''}`}
                    onClick={() => setActiveTab('billing')}
                >
                    💰 Cost & Billing
                </button>
                <button
                    className={`hover-glow ${activeTab === 'timeline' ? 'active' : ''}`}
                    onClick={() => setActiveTab('timeline')}
                >
                    📅 Medical Timeline
                </button>
                <button
                    className={`hover-glow ${activeTab === 'summary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('summary')}
                >
                    📄 Discharge Summary
                </button>
            </div>

            <div className="dashboard-content">
                {activeTab === 'billing' && (
                    <div className="tab-pane animate-fade-up">
                        <div className="cost-summary-box card teal-glow">
                            <h2 className="teal-gradient-text">Live Billing Estimate</h2>
                            <div className="total-cost">
                                <small>Estimated Total</small>
                                <strong className="teal-gradient-text animate-pulse-slow">₹{billingData.estimated_total}</strong>
                            </div>
                            <div className="duration">
                                <span>Hospital Duration: <strong>{billingData.duration_days} days</strong></span>
                            </div>

                            <div className="breakdown-list card">
                                <h3 style={{ marginBottom: '20px', fontSize: '1.2rem' }}>Fee Breakdown</h3>
                                {billingData.breakdown.map((item, idx) => (
                                    <div key={idx} className="breakdown-item animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
                                        <span>{item.category}</span>
                                        <strong>₹{item.cost}</strong>
                                    </div>
                                ))}
                            </div>
                            <p className="disclaimer-text" style={{ marginTop: '20px' }}>
                                ℹ️ This is an automated estimate based on hospital logs. Final billing may vary.
                            </p>
                        </div>

                        {billAnalysis && (
                            <div className="billing-analysis card animate-fade-up" style={{ marginTop: '40px', animationDelay: '0.2s' }}>
                                <h2 className="teal-gradient-text">AI Cost Analysis & Savings</h2>
                                <p style={{ color: 'var(--text-soft)', marginBottom: '30px' }}>We've analyzed your medical charges to find potential savings and negotiation points.</p>

                                <div className="negotiation-summary">
                                    <p>💡 <strong>Potential Savings Found!</strong> We've identifies items where costs might be negotiable or generic alternatives exist.</p>
                                </div>

                                <div className="negotiation-list">
                                    {billAnalysis.negotiation_points.map((point, idx) => (
                                        <div key={idx} className="negotiation-card card hover-glow animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
                                            <div className="negotiation-header">
                                                <strong className="teal-gradient-text">{point.item}</strong>
                                                <span className={`negotiable-badge ${point.negotiable.toLowerCase()}`}>
                                                    {point.negotiable}
                                                </span>
                                            </div>
                                            <div className="negotiation-details">
                                                <p><strong>Reasoning:</strong> {point.reasoning}</p>
                                                <div className="suggested-text">
                                                    " {point.suggested_negotiation_text} "
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'timeline' && (
                    <div className="tab-pane animate-fade-up">
                        <h2 className="section-title teal-gradient-text" style={{ marginBottom: '30px' }}>Recovery Timeline</h2>
                        <div className="timeline-view">
                            {timeline.length === 0 ? (
                                <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                                    <p className="text-muted">History logs will appear here as your treatment progresses.</p>
                                </div>
                            ) : (
                                timeline.map((item, idx) => (
                                    <div key={idx} className={`timeline-card card hover-glow animate-fade-in ${item.type}`} style={{ animationDelay: `${idx * 0.05}s` }}>
                                        <div className="date-badge">{new Date(item.date).toLocaleString()}</div>
                                        <h4 className="teal-gradient-text">{item.type.toUpperCase().replace('_', ' ')}</h4>
                                        <p style={{ marginTop: '10px' }}>{item.content}</p>
                                        {item.medicine_name && (
                                            <div className="meds">
                                                💊 Medication: <strong>{item.medicine_name}</strong>
                                            </div>
                                        )}
                                        {item.file_path && (
                                            <a
                                                href={`http://localhost:8002/${item.file_path}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="btn-buy hover-scale"
                                                style={{ display: 'inline-block', marginTop: '15px', padding: '8px 20px' }}
                                            >
                                                📄 View Medical Report
                                            </a>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'summary' && (
                    <div className="tab-pane animate-fade-up">
                        <div className="discharge-summary-view card">
                            {!dischargeSummary ? (
                                <div style={{ textAlign: 'center', padding: '40px' }}>
                                    <p className="text-muted">Your final discharge summary will be available here once finalized by the doctor.</p>
                                </div>
                            ) : (
                                <>
                                    <div className="summary-header">
                                        <h2 className="teal-gradient-text animate-slide-down">Official Discharge Summary</h2>
                                        <span className="status-badge final">Final Report</span>
                                    </div>

                                    <div className="summary-content">
                                        <div className="summary-section animate-fade-in" style={{ marginBottom: '30px' }}>
                                            <h4>Clinical Summary</h4>
                                            <div className="summary-text card">
                                                {dischargeSummary.summary_text}
                                            </div>
                                        </div>

                                        <div className="summary-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
                                            <div className="summary-section animate-fade-in" style={{ animationDelay: '0.1s' }}>
                                                <h4>Follow-up Instructions</h4>
                                                <div className="summary-text card" style={{ borderColor: 'var(--teal-primary)' }}>
                                                    {dischargeSummary.follow_up}
                                                </div>
                                            </div>
                                            <div className="summary-section animate-fade-in" style={{ animationDelay: '0.2s' }}>
                                                <h4>Dietary Advice</h4>
                                                <div className="summary-text card" style={{ borderColor: 'var(--teal-primary)' }}>
                                                    {dischargeSummary.diet_advice}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="summary-section animate-fade-in" style={{ animationDelay: '0.3s' }}>
                                            <h4 className="red-flags-title" style={{ color: '#ef4444' }}>⚠️ Red Flag Symptoms (Seek Help Immediately)</h4>
                                            <div className="summary-text red-flags card">
                                                {dischargeSummary.red_flags}
                                            </div>
                                        </div>

                                        <div style={{ marginTop: '40px', textAlign: 'center' }}>
                                            <button className="btn-primary hover-scale" onClick={handleDownloadPDF} disabled={loading} style={{ padding: '15px 40px' }}>
                                                {loading ? 'Exporting...' : '📄 Download PDF Report'}
                                            </button>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
