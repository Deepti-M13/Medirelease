// Minimal test component to verify React is working
export default function HomePage({ onNormalizeLogin }) {
    console.log('HomePage component rendering...');

    return (
        <div style={{ padding: '20px', background: '#f0f0f0', minHeight: '100vh' }}>
            <h1>🏥 Hospital Digital Platform</h1>
            <p>If you can see this, React is working!</p>
            <button onClick={onNormalizeLogin} style={{ padding: '10px 20px', fontSize: '16px' }}>
                Login to Portal
            </button>
            <div style={{ marginTop: '20px', padding: '20px', background: 'white', borderRadius: '8px' }}>
                <h2>Test Section</h2>
                <p>This is a minimal test to verify the component renders.</p>
            </div>
        </div>
    );
}
