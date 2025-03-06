class JournalStore {
    constructor() {
        this.journals = new Map();
    }

    getAllJournals() {
        return Array.from(this.journals.values());
    }

    getJournal(filename) {
        return this.journals.get(filename);
    }

    createJournal(data) {
        const filename = `${Date.now()}.json`;
        const journal = {
            filename,
            ...data,
            createdAt: new Date().toISOString()
        };
        this.journals.set(filename, journal);
        return journal;
    }

    deleteJournal(filename) {
        return this.journals.delete(filename);
    }
}

module.exports = new JournalStore(); 