import axios from 'axios';

// Use environment variable or fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api';

// Export API base URL for use in fetch calls
export const getApiBaseUrl = () => {
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';
};

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
});

// Auth APIs
export const login = async (username, password, role) => {
    const response = await api.post('/auth/login', { username, password, role });
    return response.data;
};

export const register = async (username, password, role) => {
    const response = await api.post('/auth/register', { username, password, role });
    return response.data;
};

// Doctor APIs
export const generateDischargeSummary = async (formData) => {
    // formData should be a FormData object containing:
    // - patient_name
    // - clinical_notes
    // - reports (optional file)
    const response = await api.post('/doctor/discharge-summary/generate', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const updateDischargeSummary = async (summaryId, data) => {
    const response = await api.put(`/doctor/discharge-summary/${summaryId}`, data);
    return response.data;
};

export const finalizeDischargeSummary = async (summaryId) => {
    const response = await api.post(`/doctor/discharge-summary/${summaryId}/finalize`);
    return response.data;
};

export const getDischargeSummary = async (summaryId) => {
    const response = await api.get(`/doctor/discharge-summary/${summaryId}`);
    return response.data;
};

export const listDischargeSummaries = async () => {
    const response = await api.get('/doctor/discharge-summaries');
    return response.data;
};

export const downloadDischargeSummaryPDF = async (summaryId) => {
    const response = await api.get(`/doctor/discharge-summary/${summaryId}/pdf`, {
        responseType: 'blob',
    });
    return response.data;
};

// Patient APIs
export const uploadBill = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/patient/bill/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const getBillAnalysis = async (billId) => {
    const response = await api.get(`/patient/bill/${billId}/analysis`);
    return response.data;
};

export const getMedicineAnalysis = async (billId) => {
    const response = await api.get(`/patient/medicine-analysis/${billId}`);
    return response.data;
};

export const viewDischargeSummaryPatient = async (summaryId) => {
    const response = await api.get(`/patient/discharge-summary/${summaryId}`);
    return response.data;
};

export const downloadBillAnalysisPDF = async (billId) => {
    const response = await api.get(`/patient/bill/${billId}/pdf`, {
        responseType: 'blob',
    });
    return response.data;
};

export const listBills = async () => {
    const response = await api.get('/patient/bills');
    return response.data;
};
