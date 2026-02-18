import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

/**
 * HistoryPage — Shows past analysis runs fetched from GET /api/history.
 * Props:
 *   onBack() — navigate back to the main analyze view
 *   onRestore(items) — load a past run's items into the dashboard
 */
export default function HistoryPage({ onBack, onRestore }) {
    const [runs, setRuns] = useState([])
    const [status, setStatus] = useState('loading') // loading | success | error
    const [expanded, setExpanded] = useState(null)

    useEffect(() => {
        fetch(`${API_BASE}/api/history?limit=50`)
            .then(r => r.json())
            .then(data => { setRuns(data); setStatus('success') })
            .catch(() => setStatus('error'))
    }, [])

    const handleRestore = useCallback((run) => {
        onRestore(run.items)
        onBack()
    }, [onRestore, onBack])

    const getSentimentColor = (score) => {
        if (score < 0.35) return '#ff5c7a'
        if (score < 0.65) return '#ffb547'
        return '#4ade80'
    }

    const formatDate = (iso) => {
        const d = new Date(iso)
        return d.toLocaleString('en-IN', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        })
    }

    const categoryColors = {
        'Bug': { bg: 'rgba(255,92,122,0.12)', border: 'rgba(255,92,122,0.3)', color: '#ff5c7a', emoji: '🐛' },
        'Feature': { bg: 'rgba(124,111,255,0.12)', border: 'rgba(124,111,255,0.3)', color: '#a89fff', emoji: '✨' },
        'Pain Point': { bg: 'rgba(255,181,71,0.12)', border: 'rgba(255,181,71,0.3)', color: '#ffb547', emoji: '😤' },
    }

    return (
        <div className="history-page">
            <div className="history-header">
                <button className="btn-back" onClick={onBack}>← Back</button>
                <h2 className="history-title">Analysis History</h2>
                <span className="dashboard-count">{runs.length} run{runs.length !== 1 ? 's' : ''}</span>
            </div>

            {status === 'loading' && (
                <div className="loading-state">
                    <div className="spinner" />
                    <p className="loading-text">Loading history…</p>
                </div>
            )}

            {status === 'error' && (
                <div className="error-banner">
                    <span className="error-icon">⚠️</span>
                    <p className="error-message">Could not load history. Is the API running?</p>
                </div>
            )}

            {status === 'success' && runs.length === 0 && (
                <div className="history-empty">
                    <span style={{ fontSize: 40 }}>📭</span>
                    <p>No analyses yet. Go analyze some feedback first!</p>
                </div>
            )}

            {status === 'success' && runs.length > 0 && (
                <div className="history-list">
                    {runs.map((run) => (
                        <div
                            key={run.id}
                            className={`history-run ${expanded === run.id ? 'expanded' : ''}`}
                        >
                            <div className="history-run-header" onClick={() =>
                                setExpanded(expanded === run.id ? null : run.id)
                            }>
                                <div className="history-run-meta">
                                    <span className="history-run-date">{formatDate(run.created_at)}</span>
                                    <span className="history-run-preview">{run.input_preview}</span>
                                </div>
                                <div className="history-run-right">
                                    <span className="dashboard-count">{run.item_count} item{run.item_count !== 1 ? 's' : ''}</span>
                                    <span className="history-chevron">{expanded === run.id ? '▲' : '▼'}</span>
                                </div>
                            </div>

                            {expanded === run.id && (
                                <div className="history-run-items">
                                    {run.items.map((item, i) => {
                                        const cfg = categoryColors[item.category] ?? categoryColors['Bug']
                                        const color = getSentimentColor(item.sentiment_score)
                                        return (
                                            <div key={i} className="history-item-card" style={{
                                                background: cfg.bg,
                                                borderColor: cfg.border,
                                            }}>
                                                <div className="history-item-top">
                                                    <span className="history-item-category" style={{ color: cfg.color }}>
                                                        {cfg.emoji} {item.category}
                                                    </span>
                                                    <span className="history-item-score" style={{ color }}>
                                                        {item.sentiment_score.toFixed(2)}
                                                    </span>
                                                </div>
                                                <p className="history-item-summary">{item.summary}</p>
                                            </div>
                                        )
                                    })}
                                    <button className="btn-restore" onClick={() => handleRestore(run)}>
                                        ↩ Restore this analysis
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
