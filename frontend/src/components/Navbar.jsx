import React, { useState } from 'react';
import './Navbar.css';

const Navbar = ({ onSignIn, onHome }) => {
    const [showAbout, setShowAbout] = useState(false);

    return (
        <>
            <nav className="navbar animate-slide-down">
                <div className="nav-left" onClick={onHome} style={{ cursor: 'pointer' }}>
                    <div className="logo-container hover-scale">
                        <span className="logo-text teal-gradient-text">MediRelease</span>
                    </div>
                </div>
                <div className="nav-right">
                    <button className="nav-link hover-glow" onClick={() => setShowAbout(true)}>About Us</button>
                    <button className="btn-signin btn-primary-shimmer hover-scale" onClick={onSignIn}>Sign In</button>
                </div>
            </nav>

            {showAbout && (
                <div className="modal-overlay animate-fade-in" onClick={() => setShowAbout(false)}>
                    <div className="about-modal card teal-glow animate-fade-up" onClick={e => e.stopPropagation()}>
                        <h2 className="teal-gradient-text">About MediRelease</h2>
                        <p>A modern, enterprise-grade AI healthcare platform focused on professionalism, trust, and security.</p>
                        <p>Streamlining medical documentation and cost analysis with advanced AI-driven tools.</p>
                        <button className="btn-primary btn-primary-shimmer hover-scale" onClick={() => setShowAbout(false)} style={{ marginTop: '20px' }}>Close</button>
                    </div>
                </div>
            )}
        </>
    );
};

export default Navbar;
