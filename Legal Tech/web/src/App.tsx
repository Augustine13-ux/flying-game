import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { ArrowDownTrayIcon, PencilIcon } from '@heroicons/react/24/outline';

interface FileManifest {
  id: string;
  filename: string;
  thumbnail_url: string;
  status: string;
}

function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [manifest, setManifest] = useState<FileManifest[]>([]);
  const [isPolling, setIsPolling] = useState(false);
  const [editingFile, setEditingFile] = useState<string | null>(null);
  const [newFilename, setNewFilename] = useState("");

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const formData = new FormData();
    acceptedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setJobId(response.data.job_id);
      setIsPolling(true);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    if (isPolling && jobId) {
      pollInterval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/job/${jobId}/manifest`);
          setManifest(response.data);
          
          // Stop polling if all files are processed
          if (response.data.every((file: FileManifest) => file.status === 'completed')) {
            setIsPolling(false);
          }
        } catch (error) {
          console.error('Polling failed:', error);
          setIsPolling(false);
        }
      }, 2000);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [isPolling, jobId]);

  const handleDownload = async () => {
    if (!jobId) return;
    
    try {
      const response = await axios.get(`/api/download/${jobId}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'processed_files.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleRename = async (oldFilename: string, newFilename: string) => {
    if (!jobId) return;
    
    try {
      const response = await axios.patch(`/api/job/${jobId}/rename`, {
        old_filename: oldFilename,
        new_filename: newFilename
      });
      
      // Update manifest with new filenames
      const updatedManifest = manifest.map(file => {
        if (file.filename === oldFilename) {
          return { ...file, filename: newFilename };
        }
        return file;
      });
      setManifest(updatedManifest);
      setEditingFile(null);
      setNewFilename("");
    } catch (error) {
      console.error('Rename failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                    ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}`}
                >
                  <input {...getInputProps()} />
                  {isDragActive ? (
                    <p>Drop the files here ...</p>
                  ) : (
                    <p>Drag 'n' drop some files here, or click to select files</p>
                  )}
                </div>

                {manifest.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-lg font-semibold mb-4">Processed Files</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {manifest.map((file) => (
                        <div key={file.id} className="border rounded-lg p-4">
                          <img
                            src={file.thumbnail_url}
                            alt={file.filename}
                            className="w-full h-32 object-cover rounded"
                          />
                          {editingFile === file.filename ? (
                            <div className="mt-2">
                              <input
                                type="text"
                                value={newFilename}
                                onChange={(e) => setNewFilename(e.target.value)}
                                className="w-full px-2 py-1 border rounded"
                                placeholder="New filename"
                              />
                              <div className="flex justify-end mt-2 space-x-2">
                                <button
                                  onClick={() => handleRename(file.filename, newFilename)}
                                  className="px-2 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={() => {
                                    setEditingFile(null);
                                    setNewFilename("");
                                  }}
                                  className="px-2 py-1 text-sm text-gray-600 bg-gray-200 rounded hover:bg-gray-300"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="mt-2 flex items-center justify-between">
                              <p className="text-sm truncate">{file.filename}</p>
                              <button
                                onClick={() => {
                                  setEditingFile(file.filename);
                                  setNewFilename(file.filename);
                                }}
                                className="p-1 text-gray-500 hover:text-gray-700"
                              >
                                <PencilIcon className="h-4 w-4" />
                              </button>
                            </div>
                          )}
                          <p className="text-xs text-gray-500">{file.status}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {manifest.length > 0 && manifest.every(file => file.status === 'completed') && (
                  <button
                    onClick={handleDownload}
                    className="mt-6 w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                    Download ZIP
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 