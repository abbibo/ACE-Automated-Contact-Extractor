import React, { useState } from 'react';
import { Edit2, Save, X, Phone, User, FileImage } from 'lucide-react';

const ResultsTable = ({ data, onUpdate }) => {
  const [editingIndex, setEditingIndex] = useState(null);
  const [editValues, setEditValues] = useState({});

  const startEditing = (index, item) => {
    setEditingIndex(index);
    setEditValues({ ...item });
  };

  const cancelEditing = () => {
    setEditingIndex(null);
    setEditValues({});
  };

  const saveEditing = (index) => {
    onUpdate(index, editValues);
    setEditingIndex(null);
    setEditValues({});
  };

  const handleChange = (field, value) => {
    setEditValues(prev => ({ ...prev, [field]: value }));
  };

  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <p>No contacts extracted yet. Upload some images to get started!</p>
      </div>
    );
  }

  return (
    <div className="results-container">
      <table className="results-table">
        <thead>
          <tr>
            <th><FileImage size={16} /> File</th>
            <th><User size={16} /> Name</th>
            <th><Phone size={16} /> Phone</th>
            <th>Confidence</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => {
            const isEditing = editingIndex === index;
            const confidenceClass = item.confidence > 0.8 ? 'high' : item.confidence > 0.5 ? 'medium' : 'low';

            return (
              <tr key={index} className={isEditing ? 'editing-row' : ''}>
                <td className="file-cell" title={item.filename}>{item.filename}</td>
                
                <td>
                  {isEditing ? (
                    <input 
                      type="text" 
                      value={editValues.name} 
                      onChange={(e) => handleChange('name', e.target.value)}
                      className="edit-input"
                    />
                  ) : (
                    <span className={!item.name || item.name === "Unknown" ? "placeholder-text" : ""}>
                      {item.name || "Unknown"}
                    </span>
                  )}
                </td>
                
                <td>
                  {isEditing ? (
                    <input 
                      type="text" 
                      value={editValues.phone} 
                      onChange={(e) => handleChange('phone', e.target.value)}
                      className="edit-input"
                    />
                  ) : (
                    <span className="phone-text">{item.phone}</span>
                  )}
                </td>

                <td>
                  <span className={`confidence-badge ${confidenceClass}`}>
                    {Math.round(item.confidence * 100)}%
                  </span>
                </td>

                <td className="actions-cell">
                  {isEditing ? (
                    <div className="action-buttons">
                      <button onClick={() => saveEditing(index)} className="btn-icon save" title="Save">
                        <Save size={16} />
                      </button>
                      <button onClick={cancelEditing} className="btn-icon cancel" title="Cancel">
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => startEditing(index, item)} className="btn-icon edit" title="Edit">
                      <Edit2 size={16} />
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;
