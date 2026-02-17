import React, { useCallback, useState } from 'react';
import { Upload } from 'lucide-react';

const UploadZone = ({ onFilesSelected, isProcessing }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(Array.from(e.target.files));
    }
  };

  return (
    <div 
      className={`upload-zone ${isDragging ? 'dragging' : ''} ${isProcessing ? 'processing' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('fileInput').click()}
    >
      <input 
        type="file" 
        id="fileInput" 
        multiple 
        accept="image/*" 
        onChange={handleChange} 
        style={{ display: 'none' }} 
        disabled={isProcessing}
      />
      
      <div className="upload-content">
        <Upload size={48} className="upload-icon" />
        <h3>{isProcessing ? 'Processing Images...' : 'Drag & Drop Screenshots here'}</h3>
        <p>or click to browse checks (PNG, JPG, WEBP)</p>
        {isProcessing && <div className="spinner"></div>}
      </div>
    </div>
  );
};

export default UploadZone;
