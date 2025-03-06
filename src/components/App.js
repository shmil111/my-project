import React, { useState, useEffect } from 'react';
import apiService from '../services/api-service';

function App() {
    const [journals, setJournals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadJournals();
    }, []);

    const loadJournals = async () => {
        try {
            const data = await apiService.getJournals();
            setJournals(data);
        } catch (err) {
            setError('Failed to load journals');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-4">Loading...</div>;
    if (error) return <div className="p-4 text-red-500">{error}</div>;

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-4">Modern Web Application</h1>
            <div className="bg-white shadow rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-2">Journals</h2>
                {journals.length === 0 ? (
                    <p>No journals found</p>
                ) : (
                    <ul className="space-y-2">
                        {journals.map((journal, index) => (
                            <li key={index} className="border-b pb-2">
                                <h3 className="font-medium">{journal.title}</h3>
                                <p className="text-gray-600">{journal.content}</p>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            <div className="mt-4">
                <a href="/package.json" className="text-blue-500 underline">View package.json</a>
            </div>
        </div>
    );
}

export default App;