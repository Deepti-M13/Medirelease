import { useState, useEffect, useRef } from 'react';
import useSpeechRecognition from '../hooks/useSpeechRecognition';
import { getApiBaseUrl } from '../utils/api';
import './AdminDashboard.css';

export default function AdminDashboard({ onLogout }) {
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [costSummary, setCostSummary] = useState(null);
    const [viewMode, setViewMode] = useState('list'); // 'list', 'detail', 'addPatient'

    // Form states
    const [dailyUpdate, setDailyUpdate] = useState('');
    const [meds, setMeds] = useState('');
    const [medName, setMedName] = useState('');
    const [medQty, setMedQty] = useState(1);
    const [medDuration, setMedDuration] = useState(1);
    const [reportFile, setReportFile] = useState(null);
    const [reportDesc, setReportDesc] = useState('');
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState({ type: '', text: '' });
    const [doctorFee, setDoctorFee] = useState('');
    const [selectedDoctorId, setSelectedDoctorId] = useState('');

    // Voice Input State
    const { isListening, transcript, startListening, stopListening, hasSupport } = useSpeechRecognition();
    const [previousUpdateText, setPreviousUpdateText] = useState('');

    // Handle voice transcript updates
    useEffect(() => {
        if (isListening) {
            // While listening, show combined text
            const separator = previousUpdateText && !previousUpdateText.endsWith(' ') ? ' ' : '';
            setDailyUpdate(previousUpdateText + separator + transcript);
        }
    }, [transcript, isListening, previousUpdateText]);

    const handleToggleListening = () => {
        if (isListening) {
            stopListening();
            // Final text is already in dailyUpdate via the effect
        } else {
            setPreviousUpdateText(dailyUpdate);
            startListening();
        }
    };

    // New patient form states
    const [newPatientName, setNewPatientName] = useState('');
    const [newPatientPassword, setNewPatientPassword] = useState('');
    const [newPatientConfirmPassword, setNewPatientConfirmPassword] = useState('');
    const [newPatientAge, setNewPatientAge] = useState('');
    const [newPatientGender, setNewPatientGender] = useState('');
    const [newPatientContact, setNewPatientContact] = useState('');
    const [newPatientDoctorId, setNewPatientDoctorId] = useState('');
    const [doctors, setDoctors] = useState([]);

    useEffect(() => {
        loadPatients();
        loadDoctors();
    }, []);

    const loadDoctors = async () => {
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/admin/doctors`);
            const data = await res.json();
            setDoctors(data || []);
        } catch (err) {
            console.error('Failed to load doctors', err);
        }
    };

    const loadPatients = async () => {
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/admin/patients`);
            const data = await res.json();
            setPatients(data);
        } catch (err) {
            console.error(err);
        }
    };

    const loadPatientData = async (id) => {
        try {
            // Load Timeline
            const timeRes = await fetch(`${getApiBaseUrl()}/api/admin/patient/${id}/timeline`);
            const timeData = await timeRes.json();
            setTimeline(timeData);

            // Load Cost Summary
            const costRes = await fetch(`${getApiBaseUrl()}/api/admin/patient/${id}/cost-summary`);
            const costData = await costRes.json();
            setCostSummary(costData);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSelectPatient = (patient) => {
        setSelectedPatient(patient);
        setViewMode('detail');
        loadPatientData(patient.id);
        setMsg({ type: '', text: '' });
    };

    const handleSubmitUpdate = async () => {
        if (!dailyUpdate) return;
        setLoading(true);
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/admin/daily-update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_id: selectedPatient.id,
                    update_text: dailyUpdate,
                    medications: meds
                })
            });
            if (res.ok) {
                setMsg({ type: 'success', text: 'Daily update added!' });
                setDailyUpdate('');
                setMeds('');
                loadPatientData(selectedPatient.id);
            } else {
                setMsg({ type: 'error', text: 'Failed to add update.' });
            }
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        } finally {
            setLoading(false);
        }
    };

    const handleLogMedicine = async () => {
        if (!medName) return;
        setLoading(true);
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/admin/log-medicine`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_id: selectedPatient.id,
                    medicine_name: medName,
                    quantity: parseInt(medQty),
                    duration: parseInt(medDuration)
                })
            });
            if (res.ok) {
                const data = await res.json();
                setMsg({ type: 'success', text: `Medicine logged! Cost: ₹${data.subtotal}` });
                setMedName('');
                setMedQty(1);
                loadPatientData(selectedPatient.id);
            } else {
                setMsg({ type: 'error', text: 'Failed to log medicine.' });
            }
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        } finally {
            setLoading(false);
        }
    };

    const handleUploadReport = async () => {
        if (!reportFile || !reportDesc) return;
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('patient_id', selectedPatient.id);
            formData.append('description', reportDesc);
            formData.append('file', reportFile);


            const res = await fetch(`${getApiBaseUrl()}/api/admin/upload-report`, {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                setMsg({ type: 'success', text: 'Report uploaded!' });
                setReportDesc('');
                setReportFile(null);
                loadPatientData(selectedPatient.id);
            } else {
                setMsg({ type: 'error', text: 'Failed to upload report.' });
            }
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        } finally {
            setLoading(false);
        }
    };

    const handleSetDoctorFee = async () => {
        if (!selectedDoctorId || !doctorFee) return;
        setLoading(true);
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/admin/set-doctor-fee`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    doctor_id: parseInt(selectedDoctorId),
                    fee: parseFloat(doctorFee)
                })
            });
            if (res.ok) {
                setMsg({ type: 'success', text: 'Doctor fee updated!' });
                setDoctorFee('');
                loadDoctors();
            } else {
                setMsg({ type: 'error', text: 'Failed to update fee.' });
            }
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        } finally {
            setLoading(false);
        }
    };

    const handleRecordVisit = async () => {
        if (!selectedPatient || !selectedPatient.treating_doctor_id) {
            setMsg({ type: 'error', text: 'No treating doctor assigned to this patient.' });
            return;
        }
        setLoading(true);
        try {
            const res = await fetch(`${getApiBaseUrl()}/api/admin/record-visit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_id: selectedPatient.id,
                    doctor_id: selectedPatient.treating_doctor_id
                })
            });
            if (res.ok) {
                setMsg({ type: 'success', text: 'Doctor visit recorded!' });
                loadPatientData(selectedPatient.id);
            } else {
                setMsg({ type: 'error', text: 'Failed to record visit.' });
            }
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        } finally {
            setLoading(false);
        }
    };

    const handleAddPatient = async () => {
        // Validate required fields
        if (!newPatientName || !newPatientPassword || !newPatientAge || !newPatientGender) {
            setMsg({ type: 'error', text: 'Please fill in all required fields' });
            return;
        }

        if (newPatientPassword !== newPatientConfirmPassword) {
            setMsg({ type: 'error', text: 'Passwords do not match' });
            return;
        }

        const ageVal = parseInt(newPatientAge);
        if (isNaN(ageVal) || ageVal <= 0) {
            setMsg({ type: 'error', text: 'Age must be a positive number' });
            return;
        }

        setLoading(true);
        try {
            const payload = {
                username: newPatientName,
                password: newPatientPassword,
                age: ageVal,
                gender: newPatientGender,
                contact: newPatientContact || null,
                treating_doctor_id: newPatientDoctorId ? parseInt(newPatientDoctorId) : null
            };

            const res = await fetch(`${getApiBaseUrl()}/api/admin/add-patient`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                setMsg({ type: 'success', text: `Patient "${newPatientName}" added successfully!` });
                setNewPatientName('');
                setNewPatientPassword('');
                setNewPatientConfirmPassword('');
                setNewPatientAge('');
                setNewPatientGender('');
                setNewPatientContact('');
                setNewPatientDoctorId('');
                loadPatients();
                setTimeout(() => setViewMode('list'), 1500);
            } else {
                const error = await res.json();
                setMsg({ type: 'error', text: error.detail || 'Failed to add patient' });
            }
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="admin-dashboard">
            <header className="dashboard-header">
                <h1>🛡️ Admin Dashboard</h1>
                <button onClick={onLogout} className="btn-logout">Logout</button>
            </header>

            <div className="admin-container">
                {viewMode === 'list' ? (
                    <div className="patient-list-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <h2>Select Patient</h2>
                            <button
                                onClick={() => {
                                    setViewMode('addPatient');
                                    setMsg({ type: '', text: '' });
                                }}
                                style={{
                                    padding: '10px 20px',
                                    backgroundColor: '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '5px',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                ➕ Add New Patient
                            </button>
                        </div>

                        <div className="doctor-fee-section" style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #dee2e6' }}>
                            <h3>⚙️ Manage Doctor Consultation Fees</h3>
                            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end' }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', marginBottom: '5px' }}>Select Doctor</label>
                                    <select
                                        value={selectedDoctorId}
                                        onChange={(e) => setSelectedDoctorId(e.target.value)}
                                        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
                                    >
                                        <option value="">Select Doctor</option>
                                        {doctors.map(doc => (
                                            <option key={doc.id} value={doc.id}>{doc.username}</option>
                                        ))}
                                    </select>
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', marginBottom: '5px' }}>Fee (₹)</label>
                                    <input
                                        type="number"
                                        value={doctorFee}
                                        onChange={(e) => setDoctorFee(e.target.value)}
                                        placeholder="e.g. 500"
                                        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
                                    />
                                </div>
                                <button
                                    onClick={handleSetDoctorFee}
                                    disabled={loading || !selectedDoctorId || !doctorFee}
                                    style={{ padding: '8px 20px', height: '40px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                                >
                                    Update Fee
                                </button>
                            </div>
                        </div>

                        <div className="patient-list">
                            {patients.map(p => (
                                <div key={p.id} className="patient-card" onClick={() => handleSelectPatient(p)}>
                                    <h3>
                                        {p.username}
                                        {p.role === 'past_patient' && (
                                            <span style={{ fontSize: '0.6em', backgroundColor: '#dc3545', color: 'white', padding: '2px 6px', borderRadius: '4px', marginLeft: '8px', verticalAlign: 'middle' }}>
                                                Past Patient
                                            </span>
                                        )}
                                    </h3>
                                    <p><strong>ID:</strong> {p.id}</p>
                                    {p.age && <p><strong>Age:</strong> {p.age}</p>}
                                    {p.gender && <p><strong>Gender:</strong> {p.gender}</p>}
                                    {p.treating_doctor ? (
                                        <p><strong>Treating Doctor:</strong> {p.treating_doctor}</p>
                                    ) : (
                                        <p><strong>Treating Doctor:</strong> <em>Not assigned</em></p>
                                    )}
                                    <p><strong>Admitted:</strong> {new Date(p.created_at).toLocaleDateString()}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : viewMode === 'addPatient' ? (
                    <div className="patient-detail-section">
                        <button onClick={() => setViewMode('list')} className="btn-back">← Back to List</button>
                        <h2>Add New Patient</h2>

                        {msg.text && <div className={`msg ${msg.type}`}>{msg.text}</div>}

                        <div style={{ maxWidth: '500px', margin: '30px auto', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    Patient Name/Username
                                </label>
                                <input
                                    type="text"
                                    placeholder="e.g., John Doe"
                                    value={newPatientName}
                                    onChange={(e) => setNewPatientName(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px',
                                        border: '1px solid #ccc',
                                        borderRadius: '4px',
                                        boxSizing: 'border-box'
                                    }}
                                />
                            </div>

                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    Password
                                </label>
                                <input
                                    type="password"
                                    placeholder="Enter password"
                                    value={newPatientPassword}
                                    onChange={(e) => setNewPatientPassword(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px',
                                        border: '1px solid #ccc',
                                        borderRadius: '4px',
                                        boxSizing: 'border-box'
                                    }}
                                />
                            </div>

                            <div style={{ marginBottom: '20px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                    Confirm Password
                                </label>
                                <input
                                    type="password"
                                    placeholder="Confirm password"
                                    value={newPatientConfirmPassword}
                                    onChange={(e) => setNewPatientConfirmPassword(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px',
                                        border: '1px solid #ccc',
                                        borderRadius: '4px',
                                        boxSizing: 'border-box'
                                    }}
                                />
                            </div>

                            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Age *</label>
                                    <input
                                        type="number"
                                        min="0"
                                        value={newPatientAge}
                                        onChange={(e) => setNewPatientAge(e.target.value)}
                                        placeholder="e.g., 35"
                                        style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
                                    />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Gender *</label>
                                    <select
                                        value={newPatientGender}
                                        onChange={(e) => setNewPatientGender(e.target.value)}
                                        style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
                                    >
                                        <option value="">Select</option>
                                        <option value="Male">Male</option>
                                        <option value="Female">Female</option>
                                        <option value="Other">Other</option>
                                    </select>
                                </div>
                            </div>

                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Contact (optional)</label>
                                <input
                                    type="text"
                                    placeholder="Phone or email"
                                    value={newPatientContact}
                                    onChange={(e) => setNewPatientContact(e.target.value)}
                                    style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
                                />
                            </div>

                            <div style={{ marginBottom: '20px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Assign Doctor *</label>
                                <select
                                    value={newPatientDoctorId}
                                    onChange={(e) => setNewPatientDoctorId(e.target.value)}
                                    style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
                                >
                                    <option value="">Select Doctor</option>
                                    {doctors.map(doc => (
                                        <option key={doc.id} value={doc.id}>{doc.username}</option>
                                    ))}
                                </select>
                            </div>

                            <button
                                onClick={handleAddPatient}
                                disabled={loading}
                                className="btn-action"
                                style={{
                                    width: '100%',
                                    padding: '12px',
                                    backgroundColor: '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    fontSize: '16px',
                                    fontWeight: 'bold'
                                }}
                            >
                                {loading ? 'Adding Patient...' : 'Add Patient'}
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="patient-detail-section">
                        <button onClick={() => setViewMode('list')} className="btn-back">← Back to List</button>
                        <h2>Managing: {selectedPatient?.username}</h2>
                        {selectedPatient?.role === 'past_patient' && (
                            <div style={{
                                backgroundColor: '#fff3cd',
                                color: '#856404',
                                padding: '10px 15px',
                                borderRadius: '4px',
                                marginBottom: '20px',
                                border: '1px solid #ffeeba',
                                fontWeight: 'bold',
                                textAlign: 'center'
                            }}>
                                🔒 This is a past patient's record. Editing is disabled.
                            </div>
                        )}

                        {msg.text && <div className={`msg ${msg.type}`}>{msg.text}</div>}

                        <div className="admin-grid">
                            <div className="admin-panel left">
                                {selectedPatient?.role !== 'past_patient' ? (
                                    <>
                                        <div className="action-card">
                                            <h3>📝 Add Daily Update</h3>
                                            <div className="update-input-container">
                                                <textarea
                                                    placeholder="Clinical update (e.g., Fever reduced...)"
                                                    value={dailyUpdate}
                                                    onChange={(e) => setDailyUpdate(e.target.value)}
                                                    rows="3"
                                                />
                                                {hasSupport && (
                                                    <button
                                                        className={`btn-mic ${isListening ? 'listening' : ''}`}
                                                        onClick={handleToggleListening}
                                                        title={isListening ? "Stop Listening" : "Start Voice Input"}
                                                    >
                                                        {isListening ? '🔴' : '🎤'}
                                                    </button>
                                                )}
                                            </div>
                                            <input
                                                type="text"
                                                placeholder="Medications given (comma separated)"
                                                value={meds}
                                                onChange={(e) => setMeds(e.target.value)}
                                            />
                                            <button onClick={handleSubmitUpdate} disabled={loading} className="btn-action btn-primary">
                                                {loading ? 'Adding...' : 'Add Log'}
                                            </button>
                                        </div>

                                        <div className="action-card card">
                                            <h3>💊 Log Medicine</h3>
                                            <input
                                                type="text"
                                                placeholder="Medicine Name (e.g., Dolo 650)"
                                                value={medName}
                                                onChange={(e) => setMedName(e.target.value)}
                                            />
                                            <div className="input-row" style={{ display: 'flex', gap: '10px' }}>
                                                <input
                                                    type="number"
                                                    placeholder="Qty"
                                                    value={medQty}
                                                    onChange={(e) => setMedQty(parseInt(e.target.value) || 1)}
                                                    style={{ flex: 1 }}
                                                />
                                                <input
                                                    type="number"
                                                    placeholder="Days"
                                                    value={medDuration}
                                                    onChange={(e) => setMedDuration(parseInt(e.target.value) || 1)}
                                                    style={{ flex: 1 }}
                                                />
                                            </div>
                                            <button onClick={handleLogMedicine} disabled={loading} className="btn-action btn-primary">
                                                Log Medicine
                                            </button>
                                        </div>

                                        <div className="action-card card" style={{ backgroundColor: '#e7f3ff', border: '1px solid #007bff' }}>
                                            <h3>🩺 Record Doctor Visit</h3>
                                            <p style={{ fontSize: '0.9em', color: '#666', marginBottom: '10px' }}>
                                                {selectedPatient?.treating_doctor ? `Treating Doctor: ${selectedPatient.treating_doctor}` : 'No doctor assigned'}
                                            </p>
                                            <button
                                                onClick={handleRecordVisit}
                                                disabled={loading || !selectedPatient?.treating_doctor}
                                                className="btn-action btn-primary"
                                                style={{ backgroundColor: '#007bff' }}
                                            >
                                                Mark Doctor Visited
                                            </button>
                                        </div>

                                        <div className="action-card card">
                                            <h3>📎 Upload Report</h3>
                                            <input
                                                type="text"
                                                placeholder="Report Description (e.g., Blood Test)"
                                                value={reportDesc}
                                                onChange={(e) => setReportDesc(e.target.value)}
                                            />
                                            <input
                                                type="file"
                                                onChange={(e) => setReportFile(e.target.files[0])}
                                            />
                                            <button onClick={handleUploadReport} disabled={loading} className="btn-action btn-primary">
                                                {loading ? 'Uploading...' : 'Upload Report'}
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <div className="action-card card" style={{ backgroundColor: '#f8f9fa', border: '1px solid #dee2e6' }}>
                                        <h3 style={{ color: '#6c757d' }}>ℹ️ Patient Discharged</h3>
                                        <p>This record is finalized. No further clinical logs or billing entries can be made by the admin.</p>
                                    </div>
                                )}

                                {costSummary && (
                                    <div className="cost-card card">
                                        <h3>💰 System Cost Summary</h3>
                                        <div className="cost-value">₹{costSummary.estimated_total}</div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9em', marginTop: '10px' }}>
                                            <span>Meds: ₹{costSummary.medicine_total}</span>
                                            <span>Visits: ₹{costSummary.consultation_total} ({costSummary.visit_count})</span>
                                        </div>
                                        <small style={{ display: 'block', marginTop: '10px', color: '#666' }}>
                                            {costSummary.message}
                                        </small>
                                    </div>
                                )}
                            </div>

                            <div className="admin-panel right">
                                <h3>📅 Patient Timeline</h3>
                                <div className="timeline card">
                                    {timeline.map((item, idx) => (
                                        <div key={idx} className={`timeline-item ${item.type}`}>
                                            <div className="date">{new Date(item.date).toLocaleString()}</div>
                                            <div className="content">
                                                {item.type === 'Daily Update' && (
                                                    <>
                                                        <strong>📝 Daily Update</strong>
                                                        <p>{item.content}</p>
                                                        {item.medications && <p className="meds">💊 Medications: {item.medications}</p>}
                                                    </>
                                                )}
                                                {item.type === 'Report' && (
                                                    <>
                                                        <strong>📄 Medical Report</strong>
                                                        <p>{item.content}</p>
                                                        {item.file_path && (
                                                            <a
                                                                href={`${getApiBaseUrl()}/${item.file_path}`}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="file-badge"
                                                                style={{ textDecoration: 'none', cursor: 'pointer' }}
                                                            >
                                                                📎 Download/View File
                                                            </a>
                                                        )}
                                                    </>
                                                )}
                                                {item.type === 'Medication' && (
                                                    <>
                                                        <strong>💊 Medicine Given</strong>
                                                        <p>{item.medicine_name} (Generic: {item.generic_name})</p>
                                                        <small>Qty: {item.quantity} | Duration: {item.duration} days | Cost: ₹{item.subtotal?.toFixed(2)}</small>
                                                    </>
                                                )}
                                                {item.type === 'Doctor Visit' && (
                                                    <>
                                                        <strong>🩺 Doctor Visit</strong>
                                                        <p>{item.content}</p>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                    {timeline.length === 0 && <p>No logs yet.</p>}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div >
    );
}
