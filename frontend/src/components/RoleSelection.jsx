import React from 'react';
import './RoleSelection.css';

const RoleSelection = ({ onSelectRole }) => {
    const roles = [
        {
            id: 'admin',
            title: 'Admin Access',
            description: 'Manage hospital records, doctors, and patient logs.',
            icon: '🛡️'
        },
        {
            id: 'doctor',
            title: 'Doctor Access',
            description: 'Access patient summaries and record health updates.',
            icon: '👨‍⚕️'
        },
        {
            id: 'patient',
            title: 'Patient Access',
            description: 'View your health records and track costs.',
            icon: '🏥'
        }
    ];

    return (
        <div className="role-selection-container animate-fade-in">
            <h1 className="teal-gradient-text animate-slide-down">Choose Your Access Role</h1>
            <p className="subtitle animate-fade-in" style={{ animationDelay: '0.2s' }}>Select the appropriate portal to continue</p>

            <div className="role-cards staggered-list">
                {roles.map((role, idx) => (
                    <div
                        key={role.id}
                        className="role-card card hover-glow hover-scale"
                        onClick={() => onSelectRole(role.id)}
                        style={{ animationDelay: `${idx * 0.1}s` }}
                    >
                        <div className="role-icon animate-float" style={{ animationDelay: `${idx * 0.5}s` }}>
                            {role.icon}
                        </div>
                        <h3 className="teal-gradient-text">{role.title}</h3>
                        <p>{role.description}</p>
                        <div className="hover-indicator"></div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RoleSelection;
