import { useState, useEffect } from 'react';
import {
    generateDischargeSummary,
    updateDischargeSummary,
    finalizeDischargeSummary,
    downloadDischargeSummaryPDF,
    listDischargeSummaries,
    getDischargeSummary
} from '../utils/api';
import { getApiBaseUrl } from '../utils/api';
import './DoctorDashboard.css';

export default function DoctorDashboard({ onLogout }) {
    const [myPatients, setMyPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [patientName, setPatientName] = useState('');
    const [clinicalNotes, setClinicalNotes] = useState('');
    const [reportFile, setReportFile] = useState(null);
    const [currentSummary, setCurrentSummary] = useState(null);
    const [summaryText, setSummaryText] = useState('');
    const [followUp, setFollowUp] = useState('');
    const [dietAdvice, setDietAdvice] = useState('');
    const [redFlags, setRedFlags] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [summaryList, setSummaryList] = useState([]);
    const [isListening, setIsListening] = useState(false);
    const [timeline, setTimeline] = useState([]);

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const doctorId = user.userId;

    useEffect(() => {
        loadMyPatients();
        loadSummaryList();
    }, []);

    const loadMyPatients = async () => {
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/doctor/my-patients?doctor_id=${doctorId}`);
            if (!res.ok) throw new Error('Failed to load patients');
            const data = await res.json();
            setMyPatients(data);
        } catch (err) {
            console.error('Error loading patients:', err);
            setError('Failed to load your patients');
        }
    };

    const loadSummaryList = async () => {
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/doctor/discharge-summaries?doctor_id=${doctorId}`);
            if (!res.ok) throw new Error('Failed to load summaries');
            const data = await res.json();
            setSummaryList(data);
        } catch (err) {
            console.error('Error loading summaries:', err);
        }
    };

    const handleSelectPatient = async (patient) => {
        setSelectedPatient(patient);
        setPatientName(patient.username);

        // Fetch timeline
        try {
            const res = await fetch(`http://localhost:8002/api/doctor/patient/${patient.id}/timeline`);
            if (res.ok) {
                const data = await res.json();
                setTimeline(data);
            }
        } catch (err) {
            console.error('Error fetching timeline', err);
        }
    };

    // Voice-to-text functionality
    const startVoiceInput = () => {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            setError('Voice input not supported in your browser. Please use Chrome or Edge.');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            setIsListening(true);
            setError('');
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            if (finalTranscript) {
                setClinicalNotes(prev => prev + finalTranscript);
            }
        };

        recognition.onerror = (event) => {
            setError('Voice recognition error: ' + event.error);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognition.start();

        // Store recognition instance to stop later
        window.currentRecognition = recognition;
    };

    const stopVoiceInput = () => {
        if (window.currentRecognition) {
            window.currentRecognition.stop();
            setIsListening(false);
        }
    };

    const handleGenerate = async () => {
        if (!selectedPatient || !clinicalNotes) {
            setError('Please select a patient and enter clinical notes');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const formData = new FormData();
            formData.append('patient_id', selectedPatient.id);
            formData.append('patient_name', patientName);
            formData.append('clinical_notes', clinicalNotes);
            formData.append('doctor_id', doctorId);
            if (reportFile) {
                formData.append('reports', reportFile);
            }

            const result = await generateDischargeSummary(formData);
            setCurrentSummary(result);
            setSummaryText(result.summary_text);
            setSuccess('Discharge summary generated successfully! Review and edit below.');
            loadSummaryList();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to generate summary');
        } finally {
            setLoading(false);
        }
    };

    const handleUpdate = async () => {
        if (!currentSummary) return;

        setLoading(true);
        setError('');

        try {
            const result = await updateDischargeSummary(currentSummary.id, {
                summary_text: summaryText,
                follow_up: followUp,
                diet_advice: dietAdvice,
                red_flags: redFlags,
            });
            setCurrentSummary(result);
            setSuccess('Summary updated successfully!');
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update summary');
        } finally {
            setLoading(false);
        }
    };

    const handleFinalize = async () => {
        if (!currentSummary) return;

        if (!confirm('Are you sure you want to mark this as final?')) return;

        setLoading(true);
        setError('');

        try {
            await finalizeDischargeSummary(currentSummary.id);
            setSuccess('Summary marked as final!');
            setCurrentSummary({ ...currentSummary, status: 'final' });
            loadSummaryList();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to finalize summary');
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPDF = async () => {
        if (!currentSummary) return;

        setLoading(true);
        try {
            const blob = await downloadDischargeSummaryPDF(currentSummary.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `discharge_summary_${currentSummary.id}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
            setSuccess('PDF downloaded successfully!');
        } catch (err) {
            setError('Failed to download PDF');
        } finally {
            setLoading(false);
        }
    };

    const handleLoadSummary = async (summaryId) => {
        try {
            const summary = await getDischargeSummary(summaryId);
            setCurrentSummary(summary);
            setSummaryText(summary.summary_text);
            setFollowUp(summary.follow_up || '');
            setDietAdvice(summary.diet_advice || '');
            setRedFlags(summary.red_flags || '');
            setPatientName(summary.patient_name);
        } catch (err) {
            setError('Failed to load summary');
        }
    };

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1 className="teal-gradient-text">MediRelease doctor portal</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <span className="user-welcome">Welcome, Dr. {user.username}</span>
                    <button onClick={onLogout} className="logout-btn">Logout</button>
                </div>
            </header>

            {error && <div className="alert alert-error">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}

            <div className="dashboard-content">
                <div className="section card">
                    <h2 className="teal-gradient-text">My Assigned Patients</h2>
                    {myPatients.length === 0 ? (
                        <p style={{ color: 'var(--text-soft)', padding: '20px' }}>No patients assigned to your care yet.</p>
                    ) : (
                        <div className="patient-cards-grid" style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                            gap: '20px',
                            marginTop: '20px'
                        }}>
                            {myPatients.map(patient => (
                                <div
                                    key={patient.id}
                                    className={`patient-item card ${selectedPatient?.id === patient.id ? 'teal-glow' : ''}`}
                                    onClick={() => handleSelectPatient(patient)}
                                    style={{
                                        cursor: 'pointer',
                                        borderColor: selectedPatient?.id === patient.id ? 'var(--teal-primary)' : 'var(--border-color)',
                                        background: selectedPatient?.id === patient.id ? 'rgba(20, 184, 166, 0.05)' : 'var(--bg-deep)'
                                    }}
                                >
                                    <h4 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        {patient.username}
                                        {(patient.role === 'past_patient' || patient.latest_summary_status === 'final') && (
                                            <span className="status-badge final" style={{ fontSize: '0.7rem' }}>Past Patient</span>
                                        )}
                                    </h4>
                                    <div style={{ marginTop: '10px', fontSize: '0.9rem', color: 'var(--text-soft)' }}>
                                        {patient.age && <p>Age: {patient.age}</p>}
                                        {patient.gender && <p>Gender: {patient.gender}</p>}
                                        {patient.latest_summary_status && (
                                            <p>Status: <strong className="teal-gradient-text">{patient.latest_summary_status}</strong></p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {selectedPatient && (
                    <div className="section card">
                        <h2 className="teal-gradient-text">Patient History: {selectedPatient.username}</h2>
                        <div className="timeline" style={{ marginTop: '20px' }}>
                            {timeline.length === 0 ? <p className="text-muted">No clinical history for this patient.</p> : (
                                timeline.map((item, idx) => (
                                    <div key={idx} className={`timeline-item ${item.type.toLowerCase().replace(' ', '_')}`} style={{
                                        borderLeft: '2px solid var(--border-color)',
                                        paddingLeft: '25px',
                                        marginBottom: '30px',
                                        position: 'relative'
                                    }}>
                                        <div className="date" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 'bold' }}>
                                            {new Date(item.date).toLocaleString()}
                                        </div>
                                        <div className="content card" style={{ padding: '15px', background: 'rgba(255, 255, 255, 0.02)' }}>
                                            <div style={{ marginBottom: '10px' }}>
                                                <strong className="teal-gradient-text">{item.type.toUpperCase()}</strong>
                                            </div>
                                            <p style={{ marginBottom: '10px' }}>{item.content}</p>
                                            {item.file_path && (
                                                <a
                                                    href={`http://localhost:8002/${item.file_path}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="btn-buy"
                                                    style={{ padding: '6px 15px', fontSize: '0.8rem', display: 'inline-block' }}
                                                >
                                                    📄 View Document
                                                </a>
                                            )}
                                            {item.medicine_name && (
                                                <div className="meds">
                                                    💊 {item.medicine_name} (Generic: {item.generic_name}) | Qty: {item.quantity}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                <div className="section card">
                    <h2 className="teal-gradient-text">Smart Discharge System</h2>
                    <p style={{ color: 'var(--text-soft)', marginBottom: '30px' }}>Generate professional, structured summaries using AI analysis.</p>

                    <div className="form-group">
                        <label>Patient Name</label>
                        <input
                            type="text"
                            value={patientName}
                            onChange={(e) => setPatientName(e.target.value)}
                            placeholder="Select a patient to begin..."
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label>Clinical Observations & Notes</label>
                        <div className="voice-input-container">
                            <textarea
                                value={clinicalNotes}
                                onChange={(e) => setClinicalNotes(e.target.value)}
                                placeholder="Enter detailed observations, diagnoses, and medication instructions..."
                                rows="8"
                                disabled={loading}
                            />
                            <div className="voice-controls">
                                <button
                                    onClick={isListening ? stopVoiceInput : startVoiceInput}
                                    className={`btn-voice ${isListening ? 'listening' : ''}`}
                                    disabled={loading}
                                >
                                    {isListening ? '🛑 Stop Dictation' : '🎤 Voice Entry'}
                                </button>
                                <span className="hint">💡 Use voice for faster clinical documentation</span>
                            </div>
                        </div>
                    </div>

                    <div className="form-group" style={{ marginTop: '30px' }}>
                        <label>Supporting Documents (Lab Results, Imaging)</label>
                        <input
                            type="file"
                            accept=".pdf,.jpg,.jpeg,.png"
                            onChange={(e) => setReportFile(e.target.files[0])}
                            disabled={loading}
                        />
                        {reportFile && <p className="file-name teal-gradient-text">📎 {reportFile.name}</p>}
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={loading || !selectedPatient}
                        className="btn-primary"
                        style={{ marginTop: '20px', width: '100%', padding: '15px' }}
                    >
                        {loading ? 'Analyzing & Generating...' : '✨ Create AI Discharge Summary'}
                    </button>
                    {!selectedPatient && <p style={{ textAlign: 'center', marginTop: '10px', color: '#ef4444', fontSize: '0.8rem' }}>Please select a patient first.</p>}
                </div>

                {currentSummary && (
                    <div className="section card teal-glow">
                        <div className="section-header">
                            <h2 className="teal-gradient-text">AI-Generated Summary Review</h2>
                            <span className={`status-badge ${currentSummary.status}`}>
                                {currentSummary.status}
                            </span>
                        </div>

                        <div className="info-box">
                            <p>🔍 <strong>AI Analysis Complete:</strong> Please review and refine the generated summary before finalizing.</p>
                        </div>

                        <div className="form-group">
                            <label>Structured Discharge Report</label>
                            <textarea
                                value={summaryText}
                                onChange={(e) => setSummaryText(e.target.value)}
                                rows="15"
                                disabled={loading || currentSummary.status === 'final'}
                            />
                        </div>

                        <div className="form-group">
                            <label>Follow-up & Recovery Plan</label>
                            <textarea
                                value={followUp}
                                onChange={(e) => setFollowUp(e.target.value)}
                                rows="4"
                                disabled={loading || currentSummary.status === 'final'}
                            />
                        </div>

                        <div className="form-group">
                            <label>Patient Diet & Lifestyle Advice</label>
                            <textarea
                                value={dietAdvice}
                                onChange={(e) => setDietAdvice(e.target.value)}
                                rows="4"
                                disabled={loading || currentSummary.status === 'final'}
                            />
                        </div>

                        <div className="form-group">
                            <label>⚠️ Critical Red Flags (Warning Signs)</label>
                            <textarea
                                value={redFlags}
                                onChange={(e) => setRedFlags(e.target.value)}
                                rows="4"
                                style={{ borderColor: '#ef4444' }}
                                disabled={loading || currentSummary.status === 'final'}
                            />
                        </div>

                        <div className="button-group">
                            <button
                                onClick={handleUpdate}
                                disabled={loading || currentSummary.status === 'final'}
                                className="btn-logout"
                                style={{ borderColor: 'var(--teal-primary)', color: 'var(--teal-primary)' }}
                            >
                                💾 Save Changes
                            </button>

                            <button
                                onClick={handleFinalize}
                                disabled={loading || currentSummary.status === 'final'}
                                className="btn-primary"
                            >
                                ✅ Mark as Final
                            </button>

                            <button
                                onClick={handleDownloadPDF}
                                disabled={loading}
                                className="btn-logout"
                                style={{ borderColor: '#3b82f6', color: '#3b82f6' }}
                            >
                                📄 Export PDF
                            </button>
                        </div>
                    </div>
                )}

                {summaryList.length > 0 && (
                    <div className="section">
                        <h2>Recent Discharge Summaries</h2>
                        <div className="summaries-list">
                            {summaryList.map((summary) => (
                                <div
                                    key={summary.id}
                                    className="summary-item"
                                    onClick={() => handleLoadSummary(summary.id)}
                                >
                                    <div>
                                        <strong>{summary.patient_name}</strong>
                                        <span className={`status-badge ${summary.status}`}>
                                            {summary.status}
                                        </span>
                                    </div>
                                    <small>{new Date(summary.created_at).toLocaleDateString()}</small>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
