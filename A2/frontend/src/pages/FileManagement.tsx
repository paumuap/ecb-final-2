import { useState, useRef } from 'react';

interface MedicalFile {
  id: number;
  filename: string;
  type: string;
  size: number;
  uploadedDate: string;
  patient: string;
}

interface FileManagementProps {
  apiUrl: string;
  token: string;
}

export default function FileManagement({ apiUrl, token }: FileManagementProps) {
  const [files, setFiles] = useState<MedicalFile[]>([
    {
      id: 1,
      filename: 'BRCA1_Test_Report.pdf',
      type: 'Genetic Report',
      size: 2.4,
      uploadedDate: '2026-06-01',
      patient: 'John Smith',
    },
    {
      id: 2,
      filename: 'Clinical_Assessment.pdf',
      type: 'Medical Report',
      size: 1.8,
      uploadedDate: '2026-06-05',
      patient: 'Jane Doe',
    },
    {
      id: 3,
      filename: 'Sequence_Analysis.xlsx',
      type: 'Data Analysis',
      size: 3.2,
      uploadedDate: '2026-06-08',
      patient: 'Bob Johnson',
    },
    {
      id: 4,
      filename: 'Family_History.docx',
      type: 'Clinical Notes',
      size: 1.1,
      uploadedDate: '2026-06-09',
      patient: 'Alice Williams',
    },
  ]);

  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredFiles = files.filter(file => {
    const matchesFilter = filter === 'all' || file.type === filter;
    const matchesSearch =
      file.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      file.patient.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('sheet') || type.includes('xlsx')) return '📊';
    if (type.includes('word') || type.includes('docx')) return '📝';
    if (type.includes('image')) return '🖼️';
    return '📁';
  };

  const handleUploadFiles = async () => {
    const filesToUpload = selectedFiles ?? fileInputRef.current?.files;
    if (!filesToUpload || filesToUpload.length === 0) {
      setUploadStatus('error');
      setUploadMessage('Select files first.');
      return;
    }

    try {
      setUploadStatus('loading');
      setUploadMessage(`Uploading ${filesToUpload.length} file(s)...`);

      // Upload each file individually
      const uploadPromises = Array.from(filesToUpload).map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        // Determine file type from extension
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        let fileType = 'Medical File';
        if (['pdf'].includes(ext)) fileType = 'PDF Report';
        if (['fasta', 'fa', 'fna', 'gb', 'gbk'].includes(ext)) fileType = 'Genomic Data';
        if (['xlsx', 'xls'].includes(ext)) fileType = 'Data Analysis';
        if (['docx', 'doc'].includes(ext)) fileType = 'Clinical Notes';
        if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) fileType = 'Medical Image';

        const query = new URLSearchParams({ file_type: fileType });
        const uploadUrl = `${apiUrl}/files/upload/1?${query.toString()}`;
        console.log('[FileManagement] Upload request', {
          url: uploadUrl,
          method: 'POST',
          file: {
            name: file.name,
            size: file.size,
            type: file.type,
          },
          resolvedFileType: fileType,
        });

        const response = await fetch(uploadUrl, {
          method: 'POST',
          body: formData,
        });

        console.log('[FileManagement] Upload response', {
          url: uploadUrl,
          status: response.status,
          ok: response.ok,
          statusText: response.statusText,
        });

        if (!response.ok) {
          const errorText = await response.text().catch(() => '');
          console.error('[FileManagement] Upload failed body', {
            url: uploadUrl,
            body: errorText,
          });
          let errorMsg = 'Upload failed';
          try {
            const errorData = JSON.parse(errorText);
            errorMsg = errorData.detail || errorMsg;
          } catch {}
          throw new Error(errorMsg);
        }

        return await response.json();
      });

      const results = await Promise.all(uploadPromises);

      // Add uploaded files to the list
      const newFiles: MedicalFile[] = results
        .filter(r => r && r.file)
        .map((r, idx) => ({
          id: files.length + idx + 1,
          filename: r.file.original_filename || Array.from(filesToUpload)[idx]?.name || 'Unknown',
          type: r.file.file_type || 'Medical File',
          size: (r.file.file_size || 0) / (1024 * 1024),
          uploadedDate: new Date().toISOString().split('T')[0],
          patient: 'Current Patient',
        }));
      
      if (newFiles.length > 0) {
        setFiles([...files, ...newFiles]);
      }

      setUploadStatus('success');
      setUploadMessage(`✓ Successfully uploaded ${filesToUpload.length} file(s)`);
      setSelectedFiles(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage(error instanceof Error ? error.message : 'Upload failed');
      console.error('[FileManagement] Upload error:', {
        message: error instanceof Error ? error.message : String(error),
        error,
      });
    }
  };

  return (
    <div className="file-management-container">
      <div className="page-header">
        <h2>📁 Medical File Storage (A2)</h2>
        <p>Secure storage and management of clinical documents and genomic files</p>
      </div>

      <div className="upload-section">
        <h3>Upload New File</h3>
        <div className="upload-area">
          <div className="upload-icon">📤</div>
          <p>Drag files here or click to upload</p>
          <input 
            ref={fileInputRef}
            type="file" 
            multiple 
            accept=".pdf,.docx,.xlsx,.fasta,.fa,.fna,.gb,.gbk,.jpg,.png,.gif"
            className="file-input"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                setSelectedFiles(e.target.files);
                setUploadStatus('idle');
                setUploadMessage(`Selected: ${e.target.files.length} file(s)`);
              }
            }}
          />
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <button 
              className="btn-secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadStatus === 'loading'}
            >
              Choose Files
            </button>
            <button 
              className="btn-primary"
              onClick={handleUploadFiles}
              disabled={uploadStatus === 'loading' || !selectedFiles}
            >
              {uploadStatus === 'loading' ? 'Uploading...' : 'Upload Files'}
            </button>
          </div>
          {uploadMessage && (
            <p className={`upload-message ${uploadStatus}`}>{uploadMessage}</p>
          )}
          <p className="upload-hint">
            Supported: PDF, DOCX, XLSX, FASTA, GenBank, Images (Max 50MB)
          </p>
        </div>
      </div>

      <div className="controls-section">
        <input
          type="text"
          placeholder="🔍 Search files..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="filter-buttons">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Files
          </button>
          <button
            className={`filter-btn ${filter === 'Genetic Report' ? 'active' : ''}`}
            onClick={() => setFilter('Genetic Report')}
          >
            Genetic Reports
          </button>
          <button
            className={`filter-btn ${filter === 'Medical Report' ? 'active' : ''}`}
            onClick={() => setFilter('Medical Report')}
          >
            Medical Reports
          </button>
          <button
            className={`filter-btn ${filter === 'Data Analysis' ? 'active' : ''}`}
            onClick={() => setFilter('Data Analysis')}
          >
            Data Files
          </button>
        </div>
      </div>

      <div className="files-list">
        <h3>Files ({filteredFiles.length})</h3>

        {filteredFiles.length > 0 ? (
          <div className="file-items">
            {filteredFiles.map(file => (
              <div key={file.id} className="file-item">
                <div className="file-icon">{getFileIcon(file.type)}</div>
                <div className="file-info">
                  <div className="file-name">{file.filename}</div>
                  <div className="file-meta">
                    <span className="file-type">{file.type}</span>
                    <span className="file-size">{file.size} MB</span>
                    <span className="file-date">{new Date(file.uploadedDate).toLocaleDateString()}</span>
                    <span className="file-patient">Patient: {file.patient}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-files">No files found</div>
        )}
      </div>

      <div className="storage-info">
        <h3>Storage Information</h3>
        <div className="storage-stats">
          <div className="stat">
            <span className="stat-label">Total Files:</span>
            <span className="stat-value">{files.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total Size:</span>
            <span className="stat-value">{(files.reduce((sum, f) => sum + f.size, 0)).toFixed(1)} MB</span>
          </div>
          <div className="stat">
            <span className="stat-label">Storage Used:</span>
            <span className="stat-value">45%</span>
          </div>
          <div className="stat">
            <span className="stat-label">Storage Limit:</span>
            <span className="stat-value">100 GB</span>
          </div>
        </div>

        <div className="storage-bar">
          <div className="storage-used" style={{ width: '45%' }}></div>
        </div>
      </div>

      <div className="features-grid">
        <div className="feature-card">
          <h4>🔐 Encryption</h4>
          <p>All files are encrypted at rest and in transit (HIPAA compliant)</p>
        </div>
        <div className="feature-card">
          <h4>👥 Access Control</h4>
          <p>Role-based access control ensures patient privacy and data security</p>
        </div>
        <div className="feature-card">
          <h4>📝 Audit Trail</h4>
          <p>Complete audit logs track all file access and modifications</p>
        </div>
        <div className="feature-card">
          <h4>🔄 Backup</h4>
          <p>Automatic daily backups ensure data integrity and recovery</p>
        </div>
      </div>
    </div>
  );
}
