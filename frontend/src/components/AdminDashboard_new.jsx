import { useState, useEffect } from 'react';
import './AdminDashboard.css';

export default function AdminDashboard({ onLogout }) {
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [costSummary, setCostSummary] = useState(null);
    const [viewMode, setViewMode] = useState('list'); // 'list', 'detail', 'addPatient'
    const [doctors, setDoctors] = useState([]);
    const [showEditDetails, setShowEditDetails] = useState(false);
    const [editAge, setEditAge] = useState('');
    const [editGender, setEditGender] = useState('');
    const [editDoctor, setEditDoctor] = useState('');

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
    
    // New patient form states
    const [newPatientName, setNewPatientName] = useState('');
    const [newPatientPassword, setNewPatientPassword] = useState('');
    const [newPatientConfirmPassword, setNewPatientConfirmPassword] = useState('');

    useEffect(() => {
        loadPatients();
        loadDoctors();
    }, []);

    const loadPatients = async () => {
        try {
            const res = await fetch('http://localhost:8002/api/admin/patients');
            const data = await res.json();
            setPatients(data);
        } catch (err) {
            console.error(err);
        }
    };

    const loadDoctors = async () => {
        try {
            const res = await fetch('http://localhost:8002/api/admin/doctors');
            const data = await res.json();
            setDoctors(data);
        } catch (err) {
            console.error('Error loading doctors:', err);
        }
    };

    const loadPatientData = async (id) => {
        try {
            // Load Timeline
            const timeRes = await fetch(`http://localhost:8002/api/admin/patient/${id}/timeline`);
            const timeData = await timeRes.json();
            setTimeline(timeData);

            // Load Cost Summary
            const costRes = await fetch(`http://localhost:8002/api/admin/patient/${id}/cost-summary`);
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
        setEditAge(patient.age || '');
        setEditGender(patient.gender || '');
        setEditDoctor(patient.treating_doctor_id || '');
    };

    const handleSubmitUpdate = async () => {
        if (!dailyUpdate) return;
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8002/api/admin/daily-update', {
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
            const res = await fetch('http://localhost:8002/api/admin/log-medicine', {
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

            const res = await fetch('http://localhost:8002/api/admin/upload-report', {
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

    const handleAddPatient = async () => {
        if (!newPatientName || !newPatientPassword) {
            setMsg({ type: 'error', text: 'Please fill in all fields' });
            return;
        }

        if (newPatientPassword !== newPatientConfirmPassword) {
            setMsg({ type: 'error', text: 'Passwords do not match' });
            return;
        }

        setLoading(true);
        try {
            const res = await fetch('http://localhost:8002/api/admin/add-patient', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: newPatientName,
                    password: newPatientPassword
                })
            });

            if (res.ok) {
                const data = await res.json();
                setMsg({ type: 'success', text: `Patient "${newPatientName}" added successfully!` });
                setNewPatientName('');
                setNewPatientPassword('');
                setNewPatientConfirmPassword('');
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

    const handleEditDetails = async () => {
        if (!editAge || !editGender || !editDoctor) {
            setMsg({ type: 'error', text: 'Please fill in all fields' });
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8002/api/admin/patient/${selectedPatient.id}/details`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    age: parseInt(editAge),
                    gender: editGender,
                    treating_doctor_id: parseInt(editDoctor)
                })
            });

            if (res.ok) {
                const updatedPatient = await res.json();
                setMsg({ type: 'success', text: 'Patient details updated successfully!' });
                setSelectedPatient(updatedPatient);
                setShowEditDetails(false);
                loadPatients();
            } else {
                const error = await res.json();
                setMsg({ type: 'error', text: error.detail || 'Failed to update patient details' });
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
                        <div className="patient-list">
                            {patients.map(p => (
                                <div key={p.id} className="patient-card" onClick={() => handleSelectPatient(p)}>
                                    <h3>{p.username}</h3>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <h2>Managing: {selectedPatient?.username}</h2>
                            <button 
                                onClick={() => setShowEditDetails(true)}
                                style={{
                                    padding: '10px 15px',
                                    backgroundColor: '#007bff',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                ✏️ Edit Patient Details
                            </button>
                        </div>

                        {msg.text && <div className={`msg ${msg.type}`}>{msg.text}</div>}

                        {/* Edit Patient Details Modal */}
                        {showEditDetails && (
                            <div style={{
                                position: 'fixed',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                backgroundColor: 'rgba(0, 0, 0, 0.6)',
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                zIndex: 1000
                            }}>
                                <div style={{
                                    backgroundColor: 'white',
                                    padding: '30px',
                                    borderRadius: '8px',
                                    maxWidth: '500px',
                                    width: '90%',
                                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                                }}>
                                    <h3>Edit Patient Details</h3>

                                    <div style={{ marginBottom: '15px' }}>
                                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                            Age
                                        </label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="150"
                                            placeholder="e.g., 35"
                                            value={editAge}
                                            onChange={(e) => setEditAge(e.target.value)}
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
                                            Gender
                                        </label>
                                        <select
                                            value={editGender}
                                            onChange={(e) => setEditGender(e.target.value)}
                                            style={{
                                                width: '100%',
                                                padding: '10px',
                                                border: '1px solid #ccc',
                                                borderRadius: '4px',
                                                boxSizing: 'border-box'
                                            }}
                                        >
                                            <option value="">Select Gender</option>
                                            <option value="Male">Male</option>
                                            <option value="Female">Female</option>
                                            <option value="Other">Other</option>
                                        </select>
                                    </div>

                                    <div style={{ marginBottom: '20px' }}>
                                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                            Assign Doctor
                                        </label>
                                        <select
                                            value={editDoctor}
                                            onChange={(e) => setEditDoctor(e.target.value)}
                                            style={{
                                                width: '100%',
                                                padding: '10px',
                                                border: '1px solid #ccc',
                                                borderRadius: '4px',
                                                boxSizing: 'border-box'
                                            }}
                                        >
                                            <option value="">Select Doctor</option>
                                            {doctors.map(doc => (
                                                <option key={doc.id} value={doc.id}>
                                                    {doc.username}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                                        <button
                                            onClick={() => setShowEditDetails(false)}
                                            style={{
                                                padding: '10px 20px',
                                                backgroundColor: '#6c757d',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleEditDetails}
                                            disabled={loading}
                                            style={{
                                                padding: '10px 20px',
                                                backgroundColor: '#007bff',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: loading ? 'not-allowed' : 'pointer'
                                            }}
                                        >
                                            {loading ? 'Saving...' : 'Save Details'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="admin-grid">
                            <div className="admin-panel left">
                                <div className="action-card">
                                    <h3>📝 Add Daily Update</h3>
                                    <textarea
                                        placeholder="Clinical update (e.g., Fever reduced...)"
                                        value={dailyUpdate}
                                        onChange={(e) => setDailyUpdate(e.target.value)}
                                        rows="3"
                                    />
                                    <input
                                        type="text"
                                        placeholder="Medications given (comma separated)"
                                        value={meds}
                                        onChange={(e) => setMeds(e.target.value)}
                                    />
                                    <button onClick={handleSubmitUpdate} disabled={loading} className="btn-action">
                                        {loading ? 'Adding...' : 'Add Log'}
                                    </button>
                                </div>

                                <div className="action-card">
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
                                    <button onClick={handleLogMedicine} disabled={loading} className="btn-action">
                                        Log Medicine
                                    </button>
                                </div>

                                <div className="action-card">
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
                                    <button onClick={handleUploadReport} disabled={loading} className="btn-action">
                                        {loading ? 'Uploading...' : 'Upload Report'}
                                    </button>
                                </div>

                                {costSummary && (
                                    <div className="cost-card">
                                        <h3>💰 System Cost Estimate</h3>
                                        <div className="cost-value">₹{costSummary.estimated_total}</div>
                                        <p className="days">For {costSummary.total_days} days</p>
                                        <small>Ref only. Not an invoice.</small>
                                    </div>
                                )}
                            </div>

                            <div className="admin-panel right">
                                <h3>📅 Patient Timeline</h3>
                                <div className="timeline">
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
                                                        {item.file_path && <span className="file-badge">📎 File Attached</span>}
                                                    </>
                                                )}
                                                {item.type === 'Medication' && (
                                                    <>
                                                        <strong>💊 Medicine Given</strong>
                                                        <p>{item.medicine_name} (Generic: {item.generic_name})</p>
                                                        <small>Qty: {item.quantity} | Duration: {item.duration} days | Cost: ₹{item.subtotal?.toFixed(2)}</small>
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
        </div>
    );
}
