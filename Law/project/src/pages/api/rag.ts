import { NextApiRequest, NextApiResponse } from 'next';
import { spawn } from 'child_process';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { query } = req.body;

  try {
    // Path to your Python script
    const scriptPath = path.join(process.cwd(), 'src', 'scripts', 'app', 'streamlit_app.py');
    
    // Spawn Python process
    const pythonProcess = spawn('python', [scriptPath, '--query', query]);

    let result = '';
    let error = '';

    // Collect data from Python script
    pythonProcess.stdout.on('data', (data) => {
      result += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      error += data.toString();
    });

    // Handle process completion
    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve(result);
        } else {
          reject(new Error(`Python process exited with code ${code}: ${error}`));
        }
      });
    });

    // Parse the result
    const parsedResult = JSON.parse(result);

    return res.status(200).json(parsedResult);
  } catch (error) {
    console.error('RAG Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}