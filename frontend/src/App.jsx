import { useState, useCallback } from 'react'
import FileUpload from './components/FileUpload'
import Dashboard from './components/Dashboard'
import HistoryPage from './components/HistoryPage'

const API_BASE = import.meta.env.VITE_API_URL ?? ''
const API_URL = `${API_BASE}/api/analyze`

/**
 * App — Root component.
 *
 * Views: 'analyze' | 'history'
 *
 * Analyze state machine:
 *   idle    → user hasn't uploaded a file yet
 *   ready   → file uploaded, waiting for "Analyze" click
 *   loading → API call in flight
 *   success → items received and rendered
 *   error   → API or network error
 */
export default function App() {
    const [view, setView] = useState('analyze') // 'analyze' | 'history'
    const [rawText, setRawText] = useState(null)
    const [status, setStatus] = useState('idle')
    const [items, setItems] = useState([])
    const [errorMsg, setErrorMsg] = useState(null)

    const handleUpload = useCallback((text) => {
        setRawText(text)
        setStatus(text ? 'ready' : 'idle')
        setItems([])
        setErrorMsg(null)
    }, [])

    const handleAnalyze = useCallback(async () => {
        if (!rawText) return

        setStatus('loading')
        setErrorMsg(null)

        try {
            const res = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: rawText }),
            })

            const data = await res.json()

            if (data.error) {
                setErrorMsg(data.error)
                setStatus('error')
                return
            }

            setItems(data.items ?? [])
            setStatus('success')
        } catch (err) {
            setErrorMsg('Could not reach the API. Is the Flask server running?')
            setStatus('error')
        }
    }, [rawText])

    // Restore a past run from history into the dashboard
    const handleRestore = useCallback((restoredItems) => {
        setItems(restoredItems)
        setStatus('success')
        setRawText('(restored from history)')
    }, [])

    const isLoading = status === 'loading'
    const canAnalyze = status === 'ready' || status === 'success'

    return (
        <div className="app">
            {/* ── Header ── */}
            <header className="header">
                <span className="header-logo">BetterFeedback</span>
                <div className="header-nav">
                    <button
                        className={`btn-nav ${view === 'analyze' ? 'active' : ''}`}
                        onClick={() => setView('analyze')}
                    >
                        ✦ Analyze
                    </button>
                    <button
                        className={`btn-nav ${view === 'history' ? 'active' : ''}`}
                        onClick={() => setView('history')}
                    >
                        🕐 History
                    </button>
                </div>
            </header>

            <main className="main">
                {/* ── History View ── */}
                {view === 'history' && (
                    <HistoryPage
                        onBack={() => setView('analyze')}
                        onRestore={handleRestore}
                    />
                )}

                {/* ── Analyze View ── */}
                {view === 'analyze' && (
                    <>
                        <section className="upload-section">
                            <h2>Upload Feedback</h2>
                            <FileUpload onUpload={handleUpload} disabled={isLoading} />

                            <button
                                className="btn-analyze"
                                onClick={handleAnalyze}
                                disabled={!canAnalyze || isLoading}
                            >
                                {isLoading ? 'Analyzing…' : '✦ Analyze Feedback'}
                            </button>
                        </section>

                        {isLoading && (
                            <div className="loading-state">
                                <div className="spinner" />
                                <p className="loading-text">Sending to Gemini AI — this takes a few seconds…</p>
                            </div>
                        )}

                        {status === 'error' && errorMsg && (
                            <div className="error-banner">
                                <span className="error-icon">⚠️</span>
                                <p className="error-message">{errorMsg}</p>
                            </div>
                        )}

                        {status === 'success' && (
                            <Dashboard items={items} />
                        )}
                    </>
                )}
            </main>
        </div>
    )
}
