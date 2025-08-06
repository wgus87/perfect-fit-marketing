const express = require('express');
const cors = require('cors');
const { GoogleSpreadsheet } = require('google-spreadsheet');
const sqlite3 = require('sqlite3').verbose();
const bodyParser = require('body-parser');
require('dotenv').config();

const sentiment = new Sentiment();
const tokenizer = new natural.WordTokenizer();

const app = express();
const port = process.env.PORT || 3002;

// Log all incoming requests
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

// Middleware
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type']
}));
app.use(bodyParser.json());

// Database setup
const db = new sqlite3.Database('../leads.db', (err) => {
  if (err) {
    console.error('Error connecting to database:', err);
  } else {
    console.log('Connected to SQLite database');
    // Create tables if they don't exist
    db.run(`CREATE TABLE IF NOT EXISTS leads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_name TEXT NOT NULL,
      website TEXT,
      industry TEXT,
      contact_email TEXT,
      contact_name TEXT,
      contact_title TEXT,
      phone TEXT,
      notes TEXT,
      discovered_date TEXT DEFAULT CURRENT_TIMESTAMP,
      last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
      status TEXT DEFAULT 'new'
    )`);
    
    db.run(`CREATE TABLE IF NOT EXISTS chat_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      message TEXT,
      response TEXT,
      sentiment REAL,
      intent TEXT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      agent_id TEXT,
      is_resolved BOOLEAN DEFAULT 0
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS lead_activities (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      lead_id INTEGER,
      activity_type TEXT,
      description TEXT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      agent_id TEXT,
      FOREIGN KEY(lead_id) REFERENCES leads(id)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS agent_assignments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id TEXT,
      lead_id INTEGER,
      assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      status TEXT DEFAULT 'active',
      FOREIGN KEY(lead_id) REFERENCES leads(id)
    )`);
  }
});

app.listen(port, '127.0.0.1', () => {
  console.log(`Server is running on http://127.0.0.1:${port}`);
});

// Google Sheets setup
const SPREADSHEET_ID = process.env.SPREADSHEET_ID;
const GOOGLE_SERVICE_ACCOUNT_EMAIL = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL;
const GOOGLE_PRIVATE_KEY = process.env.GOOGLE_PRIVATE_KEY;

async function getGoogleSheet() {
  const doc = new GoogleSpreadsheet(SPREADSHEET_ID);
  await doc.useServiceAccountAuth({
    client_email: GOOGLE_SERVICE_ACCOUNT_EMAIL,
    private_key: GOOGLE_PRIVATE_KEY.replace(/\\n/g, '\n'),
  });
  await doc.loadInfo();
  return doc.sheetsByIndex[0];
}

// API Endpoints

// Test endpoint
app.get('/api/test', (req, res) => {
  res.json({ status: 'ok' });
});

// Submit new lead
app.post('/api/leads', async (req, res) => {
  console.log('Received lead:', req.body);
  
  if (!req.body.company_name) {
    return res.status(400).json({ error: 'company_name is required' });
  }
  const { 
    company_name, 
    website,
    industry,
    contact_email,
    contact_name,
    contact_title,
    phone,
    notes
  } = req.body;
  
  try {
    console.log('Starting database save...');
    // Save to SQLite
    db.run(
      `INSERT INTO leads (
        company_name, website, industry, contact_email, 
        contact_name, contact_title, phone, notes
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [company_name, website, industry, contact_email, contact_name, contact_title, phone, notes],
      async function(err) {
        if (err) {
          console.error('Error saving to database:', err);
          return res.status(500).json({ error: 'Error saving lead' });
        }

        // Save to Google Sheets
        try {
          const sheet = await getGoogleSheet();
          await sheet.addRow({
            ID: this.lastID,
            Company: company_name,
            Website: website,
            Industry: industry,
            Email: contact_email,
            Contact: contact_name,
            Title: contact_title,
            Phone: phone,
            Notes: notes,
            Timestamp: new Date().toISOString(),
            Status: 'new'
          });

          res.status(200).json({ 
            message: 'Lead saved successfully',
            leadId: this.lastID 
          });
        } catch (sheetError) {
          console.error('Error saving to Google Sheets:', sheetError);
          // Still return success since we saved to SQLite
          res.status(200).json({ 
            message: 'Lead saved to database',
            leadId: this.lastID,
            warning: 'Failed to sync with spreadsheet'
          });
        }
      }
    );
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Chat endpoint
app.post('/api/chat', async (req, res) => {
  const { message, userId } = req.body;

  try {
    // Analyze sentiment
    const sentimentResult = sentiment.analyze(message);
    const sentimentScore = sentimentResult.comparative;

    // Analyze intent
    const tokens = tokenizer.tokenize(message.toLowerCase());
    const intents = {
      question: tokens.some(t => ['what', 'how', 'when', 'where', 'why', 'who'].includes(t)),
      urgent: tokens.some(t => ['urgent', 'asap', 'emergency', 'immediately'].includes(t)),
      interest: tokens.some(t => ['interested', 'want', 'looking', 'need'].includes(t)),
      complaint: tokens.some(t => ['problem', 'issue', 'wrong', 'bad', 'unhappy'].includes(t))
    };
    const primaryIntent = Object.entries(intents).find(([_, value]) => value)?.[0] || 'general';

    // Store message in database
    db.run(
      'INSERT INTO chat_messages (user_id, message, sentiment, intent) VALUES (?, ?, ?, ?)',
      [userId, message, sentimentScore, primaryIntent],
      async function(err) {
        if (err) {
          console.error('Error saving chat message:', err);
          return res.status(500).json({ error: 'Error saving message' });
        }

        // Determine response based on sentiment and intent
        let response;
        if (intents.urgent && sentimentScore < 0) {
          response = "I understand this is urgent. Let me connect you with a customer service agent right away.";
        } else if (intents.complaint) {
          response = "I'm sorry to hear you're experiencing issues. A customer service representative will assist you shortly.";
        } else if (intents.question) {
          response = "Thank you for your question. I'll help you find the information you need.";
        } else if (intents.interest) {
          response = "That's great! I'll connect you with one of our specialists who can provide more information.";
        } else {
          response = "Thank you for your message. A customer service representative will be with you shortly.";
        }

        // Update message with response
        db.run(
          'UPDATE chat_messages SET response = ? WHERE id = ?',
          [response, this.lastID]
        );

        res.status(200).json({ 
          response,
          sentiment: sentimentScore,
          intent: primaryIntent
        });
      }
    );
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get all leads
app.get('/api/leads', (req, res) => {
  db.all('SELECT * FROM leads ORDER BY timestamp DESC', [], (err, rows) => {
    if (err) {
      console.error('Error fetching leads:', err);
      return res.status(500).json({ error: 'Error fetching leads' });
    }
    res.json(rows);
  });
});

// Update lead status
app.put('/api/leads/:id', async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;

  try {
    db.run(
      'UPDATE leads SET status = ? WHERE id = ?',
      [status, id],
      async function(err) {
        if (err) {
          console.error('Error updating lead:', err);
          return res.status(500).json({ error: 'Error updating lead' });
        }

        // Update Google Sheets
        try {
          const sheet = await getGoogleSheet();
          const rows = await sheet.getRows();
          const row = rows.find(r => r.ID === id);
          if (row) {
            row.Status = status;
            await row.save();
          }
        } catch (sheetError) {
          console.error('Error updating Google Sheets:', sheetError);
        }

        res.json({ message: 'Lead updated successfully' });
      }
    );
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Get lead activities
app.get('/api/leads/:id/activities', (req, res) => {
  const { id } = req.params;
  db.all(
    'SELECT * FROM lead_activities WHERE lead_id = ? ORDER BY timestamp DESC',
    [id],
    (err, rows) => {
      if (err) {
        console.error('Error fetching lead activities:', err);
        return res.status(500).json({ error: 'Error fetching lead activities' });
      }
      res.json(rows);
    }
  );
});

// Add lead activity
app.post('/api/leads/:id/activities', (req, res) => {
  const { id } = req.params;
  const { activity_type, description, agent_id } = req.body;

  db.run(
    'INSERT INTO lead_activities (lead_id, activity_type, description, agent_id) VALUES (?, ?, ?, ?)',
    [id, activity_type, description, agent_id],
    function(err) {
      if (err) {
        console.error('Error adding lead activity:', err);
        return res.status(500).json({ error: 'Error adding lead activity' });
      }
      res.json({ 
        message: 'Activity added successfully',
        activityId: this.lastID 
      });
    }
  );
});

// Assign lead to agent
app.post('/api/leads/:id/assign', (req, res) => {
  const { id } = req.params;
  const { agent_id } = req.body;

  db.serialize(() => {
    // Update lead assignment
    db.run(
      'UPDATE leads SET assigned_to = ? WHERE id = ?',
      [agent_id, id],
      (err) => {
        if (err) {
          console.error('Error assigning lead:', err);
          return res.status(500).json({ error: 'Error assigning lead' });
        }

        // Create assignment record
        db.run(
          'INSERT INTO agent_assignments (agent_id, lead_id) VALUES (?, ?)',
          [agent_id, id],
          function(err) {
            if (err) {
              console.error('Error creating assignment record:', err);
              return res.status(500).json({ error: 'Error creating assignment record' });
            }

            // Add activity
            db.run(
              'INSERT INTO lead_activities (lead_id, activity_type, description, agent_id) VALUES (?, ?, ?, ?)',
              [id, 'assignment', `Lead assigned to agent ${agent_id}`, agent_id],
              function(err) {
                if (err) {
                  console.error('Error adding assignment activity:', err);
                }
              }
            );

            res.json({ message: 'Lead assigned successfully' });
          }
        );
      }
    );
  });
});

// Update lead score
app.put('/api/leads/:id/score', async (req, res) => {
  const { id } = req.params;
  const { score } = req.body;

  try {
    db.run(
      'UPDATE leads SET lead_score = ? WHERE id = ?',
      [score, id],
      async function(err) {
        if (err) {
          console.error('Error updating lead score:', err);
          return res.status(500).json({ error: 'Error updating lead score' });
        }

        // Update Google Sheets
        try {
          const sheet = await getGoogleSheet();
          const rows = await sheet.getRows();
          const row = rows.find(r => r.ID === id);
          if (row) {
            row.LeadScore = score;
            await row.save();
          }
        } catch (sheetError) {
          console.error('Error updating Google Sheets:', sheetError);
        }

        res.json({ message: 'Lead score updated successfully' });
      }
    );
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Add notes to lead
app.post('/api/leads/:id/notes', (req, res) => {
  const { id } = req.params;
  const { notes, agent_id } = req.body;

  db.run(
    'UPDATE leads SET notes = COALESCE(notes || CHAR(10) || ?, ?) WHERE id = ?',
    [`[Agent ${agent_id}]: ${notes}`, `[Agent ${agent_id}]: ${notes}`, id],
    function(err) {
      if (err) {
        console.error('Error adding notes:', err);
        return res.status(500).json({ error: 'Error adding notes' });
      }

      // Add activity
      db.run(
        'INSERT INTO lead_activities (lead_id, activity_type, description, agent_id) VALUES (?, ?, ?, ?)',
        [id, 'note', 'Added notes', agent_id]
      );

      res.json({ message: 'Notes added successfully' });
    }
  );
});

// Get chat history for a user
app.get('/api/chat/:userId/history', (req, res) => {
  const { userId } = req.params;
  db.all(
    'SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp ASC',
    [userId],
    (err, rows) => {
      if (err) {
        console.error('Error fetching chat history:', err);
        return res.status(500).json({ error: 'Error fetching chat history' });
      }
      res.json(rows);
    }
  );
});

// Mark chat as resolved
app.put('/api/chat/:messageId/resolve', (req, res) => {
  const { messageId } = req.params;
  const { agent_id } = req.body;

  db.run(
    'UPDATE chat_messages SET is_resolved = 1, agent_id = ? WHERE id = ?',
    [agent_id, messageId],
    (err) => {
      if (err) {
        console.error('Error resolving chat:', err);
        return res.status(500).json({ error: 'Error resolving chat' });
      }
      res.json({ message: 'Chat marked as resolved' });
    }
  );
});

// Get agent's assigned leads
app.get('/api/agents/:agentId/leads', (req, res) => {
  const { agentId } = req.params;
  db.all(
    'SELECT * FROM leads WHERE assigned_to = ? ORDER BY timestamp DESC',
    [agentId],
    (err, rows) => {
      if (err) {
        console.error('Error fetching agent leads:', err);
        return res.status(500).json({ error: 'Error fetching agent leads' });
      }
      res.json(rows);
    }
  );
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
