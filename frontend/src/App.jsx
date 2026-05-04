import React, { useState } from 'react';
import UploadZone from './components/UploadZone';
import ResultsTable from './components/ResultsTable';
import * as XLSX from 'xlsx';
import { Download, FileText, Smartphone, Table } from 'lucide-react';
import './index.css';

function App() {
  const [results, setResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState({ current: 0, total: 0 });
  const [mode, setMode] = useState('extract'); // 'extract' or 'process'

  // Helper to upload a single file with retries
  const uploadFile = async (file, retryCount = 0) => {
    const formData = new FormData();
    formData.append('files', file); // API expects list, but we send one by one

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const apiUrl = import.meta.env.VITE_API_URL || 'https://abeypaul13-ace-backend.hf.space';
      xhr.open('POST', `${apiUrl}/extract`);
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve(data.results || []);
          } catch {
            reject(new Error('Invalid JSON response. The backend might be sleeping or down.'));
          }
        } else {
          // Retry on server errors
          if (retryCount < 2 && xhr.status >= 500) {
             console.warn(`Retrying ${file.name} (Attempt ${retryCount + 2})...`);
             resolve(uploadFile(file, retryCount + 1));
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        }
      };

      xhr.onerror = () => {
         if (retryCount < 2) {
             console.warn(`Retrying ${file.name} (Attempt ${retryCount + 2})...`);
             resolve(uploadFile(file, retryCount + 1));
         } else {
             reject(new Error('Network error'));
         }
      };

      xhr.send(formData);
    });
  };

  const handleFilesSelected = async (files) => {
    if (files.length === 0) return;

    setIsProcessing(true);
    setProcessingStatus({ current: 0, total: files.length });
    setUploadProgress(0);
    
    let uploadedCount = 0;
    
    // Process sequentially
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const fileResults = await uploadFile(file);
        
        // Deduplication Logic:
        // Filter out contacts that already exist in the current results state.
        // We check if the phone number already exists in 'results'.
        setResults(prev => {
          const existingPhones = new Set(prev.map(r => r.phone));
          const newContacts = fileResults.filter(contact => {
             // If phone is empty, we might keep it or drop it. Let's keep for now as per backend logic.
             // But if it has a phone, check uniqueness.
             if (!contact.phone) return true; 
             return !existingPhones.has(contact.phone);
          });
          return [...prev, ...newContacts];
        });

        uploadedCount++;
        
        // Update progress strictly based on completed count
        setProcessingStatus(prev => ({ ...prev, current: uploadedCount }));
        setUploadProgress(Math.round((uploadedCount / files.length) * 100));
        
      } catch (error) {
        console.error(`Failed to process ${file.name}:`, error);
        // Do NOT increment uploadedCount or progress for failed files
        // But we continue to the next file
        alert(`Failed to process ${file.name}: ${error.message}`);
      }
    }

    setIsProcessing(false);
  };

  const handleDatasetSelected = async (files) => {
    if (files.length === 0) return;
    const file = files[0]; // Only process one dataset at a time for now

    setIsProcessing(true);
    setUploadProgress(0);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://abeypaul13-ace-backend.hf.space'}/process-dataset`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
             throw new Error(JSON.parse(errorText).detail || 'Failed to process dataset');
        }

        // Handle file download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processed_${file.name.replace('.csv', '').replace('.xlsx', '')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert('Dataset processed and downloaded successfully!');

    } catch (error) {
        console.error('Dataset processing failed:', error);
        alert(`Error: ${error.message}`);
    } finally {
        setIsProcessing(false);
        setUploadProgress(100);
    }
  };

  const handleUpdate = (index, newValues) => {
    setResults(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], ...newValues };
      return updated;
    });
  };

  const handleExport = () => {
    if (results.length === 0) return;

    // Filter data for export (exclude raw fields if needed, but we keep them clean)
    const exportData = results.map(({ name, phone }) => ({
      Name: name,
      Phone: phone
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Contacts");
    
    // Generate filename with timestamp
    const date = new Date().toISOString().slice(0,10);
    XLSX.writeFile(workbook, `ACE_Contacts_${date}.xlsx`);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo">
          <Smartphone size={32} className="logo-icon" />
          <h1>ACE <span className="subtitle">Automated Contact Extractor</span></h1>
        </div>
        <button 
          className="btn-primary export-btn" 
          onClick={handleExport}
          disabled={results.length === 0}
        >
          <Download size={18} /> Export to Excel
        </button>
      </header>

      <main className="main-content">
        <div className="mode-toggle">
            <button 
                className={`mode-btn ${mode === 'extract' ? 'active' : ''}`}
                onClick={() => setMode('extract')}
            >
                <Smartphone size={18} /> Extract from Images
            </button>
            <button 
                className={`mode-btn ${mode === 'process' ? 'active' : ''}`}
                onClick={() => setMode('process')}
            >
                <Table size={18} /> Process Dataset
            </button>
        </div>

        <section className="upload-section">
          {mode === 'extract' ? (
              <UploadZone 
                onFilesSelected={handleFilesSelected} 
                isProcessing={isProcessing}
                accept="image/*"
                title="Drag & Drop Screenshots here"
                subtitle="or click to browse images (PNG, JPG, WEBP)"
              />
          ) : (
              <UploadZone 
                onFilesSelected={handleDatasetSelected} 
                isProcessing={isProcessing} 
                accept=".csv, .xls, .xlsx"
                title="Drag & Drop Dataset here"
                subtitle="or click to browse files (CSV, Excel)"
              />
          )}

          {isProcessing && mode === 'extract' && (
            <div className="progress-container">
              <div className="progress-label">
                <span>Uploading file {processingStatus.current} of {processingStatus.total}</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="progress-track">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}
           {isProcessing && mode === 'process' && (
            <div className="progress-container">
               <div className="progress-label">
                <span>Processing dataset...</span>
                <span>Please wait</span>
              </div>
              <div className="progress-track">
                <div 
                  className="progress-fill processing" 
                  style={{ width: '100%' }}
                ></div>
              </div>
            </div>
          )}
        </section>

        {mode === 'extract' && (
            <section className="results-section">
            <div className="section-header">
                <h2>Extracted Contacts <span className="count-badge">{results.length}</span></h2>
            </div>
            <ResultsTable data={results} onUpdate={handleUpdate} />
            </section>
        )}
      </main>
      
      <footer className="app-footer">
        <p>&copy; 2026 — Web application engineered and maintained by Zaptockz; all rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
