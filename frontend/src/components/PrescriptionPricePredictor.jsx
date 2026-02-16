import React, { useState } from 'react';
import axios from 'axios';
import { getApiBaseUrl } from '../utils/api';
import './PrescriptionPricePredictor.css';

const PrescriptionPricePredictor = () => {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');
    const [manualInput, setManualInput] = useState('');

    const handleCompare = async () => {
        if (!manualInput.trim()) {
            setError('Please enter a medicine name.');
            return;
        }

        setLoading(true);
        setError('');
        setResults(null);

        try {
            const response = await axios.post(`${getApiBaseUrl()}/api/prescription/compare-prices-manual`, {
                medicine_names: [manualInput.trim()]
            });
            setResults(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to fetch price comparison. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="price-predictor-card card">
            <div className="flow-visualizer">
                <div className="flow-step">
                    <div className="icon-circle">✍️</div>
                    <span>Enter Name</span>
                </div>
                <div className="flow-line"></div>
                <div className="flow-step">
                    <div className={`icon-circle ${loading ? 'pulse' : ''}`}>🌐</div>
                    <span>Web Scrape</span>
                </div>
                <div className="flow-line"></div>
                <div className="flow-step">
                    <div className="icon-circle">💰</div>
                    <span>View Prices</span>
                </div>
            </div>

            <div className="predictor-input-section">
                <div className="input-with-button">
                    <input
                        type="text"
                        value={manualInput}
                        onChange={(e) => setManualInput(e.target.value)}
                        placeholder="e.g., Dolo 650, Atorvastatin..."
                        className="predictor-input"
                    />
                    <button
                        onClick={handleCompare}
                        disabled={loading || !manualInput.trim()}
                        className="btn-primary"
                    >
                        {loading ? 'Searching...' : 'Compare Prices'}
                    </button>
                </div>
                {error && <p className="predictor-error">{error}</p>}
            </div>

            {results && (
                <div className="predictor-results">
                    {results.medicines_found.map((med, idx) => (
                        <div key={idx} className="med-result-group">
                            <h4 className="med-title">{med}</h4>
                            <div className="comparison-grid">
                                {results.results[med] && results.results[med].map((site, sIdx) => (
                                    <div key={sIdx} className="comparison-card">
                                        <div className="site-info">
                                            <span className="site-badge">{site.site_name}</span>
                                            <span className="med-price">₹{site.price}</span>
                                        </div>
                                        <a href={site.link} target="_blank" rel="noopener noreferrer" className="btn-buy">
                                            View Deal
                                        </a>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default PrescriptionPricePredictor;
