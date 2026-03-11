import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import { dirname, join } from 'path';

// Configure dotenv with absolute path
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const envPath = join(__dirname, '.env');

// Load environment variables
dotenv.config({ path: envPath });

// Debug environment variables
console.log('Environment variables loaded from:', envPath);
console.log('OPENAI_API_KEY present:', !!process.env.OPENAI_API_KEY);
console.log('OPENAI_MODEL:', process.env.OPENAI_MODEL);

// Check if API key is present
if (!process.env.OPENAI_API_KEY) {
  throw new Error('OPENAI_API_KEY is not set in environment variables');
}

// Initialize Express app
const app = express();
app.use(cors());
app.use(express.json());

// Initialize OpenAI (only once)
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

app.post('/api/chat', async (req, res) => {
  try {
    const { messages } = req.body;
    const latestMessage = messages[messages.length - 1].content;

    // Path to your Python script
    const scriptPath = path.join(__dirname, '..', 'src', 'scripts', 'app', 'rag_pipeline.py');
    
    // Spawn Python process
    const pythonProcess = spawn('python', [scriptPath, '--query', latestMessage]);

    let result = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
      result += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      error += data.toString();
      console.error(`Python Error: ${error}`);
    });

    // Wait for Python process to complete
    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Python process exited with code ${code}`));
        }
      });
    });

    // Use RAG results in OpenAI completion
    const completion = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-4",
      messages: [
        {
          role: "system",
          content: `You are a legal assistant. Use the following context to answer questions: ${result}`
        },
        ...messages
      ],
      temperature: 0.7,
    });

    res.json({ 
      message: completion.choices[0].message.content,
      sources: result.sources || [] 
    });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'An error occurred while processing your request.' });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});