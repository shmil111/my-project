const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const path = require('path');
const env = require('./utils/env');
const apiService = require('./services/api-service');

const app = express();

// Middleware
app.use(helmet()); // Security headers
app.use(cors()); // Enable CORS
app.use(express.json()); // Parse JSON bodies
app.use(morgan('dev')); // Logging

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, '../public')));

// API routes
app.get('/api/health', async (req, res) => {
    try {
        const health = await apiService.checkHealth();
        res.json(health);
    } catch (error) {
        res.status(500).json({ error: 'Health check failed' });
    }
});

app.get('/api/journals', async (req, res) => {
    try {
        const journals = await apiService.getJournals();
        res.json(journals);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch journals' });
    }
});

app.get('/api/journals/:filename', async (req, res) => {
    try {
        const journal = await apiService.getJournal(req.params.filename);
        res.json(journal);
    } catch (error) {
        res.status(404).json({ error: 'Journal not found' });
    }
});

app.post('/api/journals', async (req, res) => {
    try {
        const journal = await apiService.createJournal(req.body);
        res.status(201).json(journal);
    } catch (error) {
        res.status(500).json({ error: 'Failed to create journal' });
    }
});

app.delete('/api/journals/:filename', async (req, res) => {
    try {
        await apiService.deleteJournal(req.params.filename);
        res.status(204).send();
    } catch (error) {
        res.status(500).json({ error: 'Failed to delete journal' });
    }
});

// Serve the React app for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

// Start server
const PORT = env.port;
const HOST = env.host;

app.listen(PORT, HOST, () => {
    console.log(`Server running at http://${HOST}:${PORT}`);
    console.log(`Environment: ${env.nodeEnv}`);
}); 