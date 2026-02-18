import { useState, useCallback } from 'react'

/**
 * FileUpload — Drag-and-drop or click-to-upload area.
 * Accepts .txt and .json files, reads content, calls onUpload(text).
 */
export default function FileUpload({ onUpload, disabled }) {
    const [dragOver, setDragOver] = useState(false)
    const [fileName, setFileName] = useState(null)
    const [fileSize, setFileSize] = useState(null)

    const readFile = useCallback((file) => {
        if (!file) return

        const validTypes = ['text/plain', 'application/json', '']
        const validExts = ['.txt', '.json']
        const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()

        if (!validExts.includes(ext)) {
            alert('Please upload a .txt or .json file.')
            return
        }

        setFileName(file.name)
        setFileSize((file.size / 1024).toFixed(1) + ' KB')

        const reader = new FileReader()
        reader.onload = (e) => {
            let text = e.target.result
            // If JSON, pretty-print it as a string for the AI
            if (ext === '.json') {
                try {
                    const parsed = JSON.parse(text)
                    text = JSON.stringify(parsed, null, 2)
                } catch {
                    // Not valid JSON — pass raw text anyway
                }
            }
            onUpload(text)
        }
        reader.readAsText(file)
    }, [onUpload])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        readFile(file)
    }, [readFile])

    const handleChange = (e) => readFile(e.target.files[0])

    const handleClear = (e) => {
        e.stopPropagation()
        setFileName(null)
        setFileSize(null)
        onUpload(null)
    }

    return (
        <div
            className={`file-upload ${dragOver ? 'drag-over' : ''} ${fileName ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
        >
            <input
                type="file"
                accept=".txt,.json"
                onChange={handleChange}
                disabled={disabled}
            />

            <span className="upload-icon">{fileName ? '📄' : '☁️'}</span>

            {fileName ? (
                <>
                    <p className="upload-title">File ready</p>
                    <div className="file-info">
                        <span className="file-badge">📎 {fileName} · {fileSize}</span>
                        <button className="btn-clear" onClick={handleClear} disabled={disabled}>
                            ✕ Clear
                        </button>
                    </div>
                </>
            ) : (
                <>
                    <p className="upload-title">Drop your feedback file here</p>
                    <p className="upload-subtitle">or click to browse — .txt or .json accepted</p>
                </>
            )}
        </div>
    )
}
