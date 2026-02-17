import React, { useState } from 'react';
import UploadZone from './components/UploadZone';
import ResultsTable from './components/ResultsTable';
import * as XLSX from 'xlsx';
import { Download, FileText, Smartphone } from 'lucide-react';
import './index.css';

function App() {
  const [results, setResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState({ current: 0, total: 0 });

  // Helper to upload a single file with retries
  const uploadFile = async (file, retryCount = 0) => {
    const formData = new FormData();
    formData.append('files', file); // API expects list, but we send one by one

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const apiUrl = import.meta.env.VITE_API_URL || '';
      xhr.open('POST', `${apiUrl}/extract`);
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve(data.results || []);
          } catch (e) {
            reject(new Error('Failed to parse response'));
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
        setResults(prev => [...prev, ...fileResults]);
        uploadedCount++;
        
        // Update progress strictly based on completed count
        setProcessingStatus(prev => ({ ...prev, current: uploadedCount }));
        setUploadProgress(Math.round((uploadedCount / files.length) * 100));
        
      } catch (error) {
        console.error(`Failed to process ${file.name}:`, error);
        // Do NOT increment uploadedCount or progress for failed files
        // But we continue to the next file
        alert(`Failed to process ${file.name} after retries.`);
      }
    }

    setIsProcessing(false);
    // Ensure 100% only if all processed (or logic dictates completion)
    // If some failed, bar might not reach 100%, which is correct per requirements
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
        <section className="upload-section">
          <UploadZone onFilesSelected={handleFilesSelected} isProcessing={isProcessing} />
          {isProcessing && (
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
        </section>

        <section className="results-section">
          <div className="section-header">
            <h2>Extracted Contacts <span className="count-badge">{results.length}</span></h2>
          </div>
          <ResultsTable data={results} onUpdate={handleUpdate} />
        </section>
      </main>
      
      <footer className="app-footer">
        <p>&copy; 2026 — Web application engineered and maintained by Zaptockz; all rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
