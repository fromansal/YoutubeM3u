const express = require('express')
const { exec } = require('child_process');
const fs = require('fs');
const app = express()

// Basic route
app.get('/', (req, res) => {
  res.send('Server is running')
})

// Update playlist route
app.get('/update', (req, res) => {
  console.log('Starting playlist update...');
  exec('python3 update_playlist.py', (error, stdout, stderr) => {
    if (error) {
      console.error('Error:', error);
      return res.status(500).json({ error: 'Update failed' });
    }
    console.log('Update complete');
    res.json({ status: 'success', output: stdout });
  });
})

// Get playlist route
app.get('/playlist', (req, res) => {
  try {
    const content = fs.readFileSync('playlist.m3u', 'utf8');
    res.type('text/plain').send(content);
  } catch (error) {
    res.status(404).send('Playlist not found. Please run /update first');
  }
})

// Download playlist route
app.get('/download', (req, res) => {
  try {
    res.download('playlist.m3u', 'playlist.m3u', (err) => {
      if (err) {
        res.status(500).send('Error downloading file');
      }
    });
  } catch (error) {
    res.status(404).send('Playlist not found. Please run /update first');
  }
})

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
})
