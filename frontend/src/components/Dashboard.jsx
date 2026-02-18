import { useState } from 'react'

// ── Sentiment helpers ────────────────────────────────────────────────────────

function getSentimentColor(score) {
    if (score < 0.35) return '#ff5c7a'
    if (score < 0.65) return '#ffb547'
    return '#4ade80'
}

function getSentimentLabel(score) {
    if (score < 0.35) return 'Negative'
    if (score < 0.65) return 'Neutral'
    return 'Positive'
}

// ── FeedbackCard ─────────────────────────────────────────────────────────────

function FeedbackCard({ item, columnClass }) {
    const [showOriginal, setShowOriginal] = useState(false)
    const color = getSentimentColor(item.sentiment_score)

    return (
        <div className={`feedback-card ${columnClass}`}>
            <p className="card-summary">{item.summary}</p>

            <div className="sentiment-row">
                <span className="sentiment-label">Sentiment</span>
                <div className="sentiment-bar-track">
                    <div
                        className="sentiment-bar-fill"
                        style={{
                            width: `${item.sentiment_score * 100}%`,
                            background: `linear-gradient(90deg, ${color}88, ${color})`,
                        }}
                    />
                </div>
                <span className="sentiment-score" style={{ color }}>
                    {item.sentiment_score.toFixed(2)}
                </span>
            </div>

            <button
                className="original-toggle"
                onClick={() => setShowOriginal((v) => !v)}
            >
                {showOriginal ? '▲ Hide' : '▼ Show'} original text
            </button>

            {showOriginal && (
                <blockquote className="original-text">"{item.original_text}"</blockquote>
            )}
        </div>
    )
}

// ── Column ───────────────────────────────────────────────────────────────────

const COLUMN_CONFIG = {
    Bug: { emoji: '🐛', label: 'Bugs', cls: 'bug' },
    Feature: { emoji: '✨', label: 'Feature Requests', cls: 'feature' },
    'Pain Point': { emoji: '😤', label: 'Pain Points', cls: 'pain' },
}

function Column({ category, items }) {
    const { emoji, label, cls } = COLUMN_CONFIG[category]

    return (
        <div className="column">
            <div className={`column-header ${cls}`}>
                <span className="column-label">
                    <span className="column-emoji">{emoji}</span>
                    {label}
                </span>
                <span className={`column-badge ${cls}`}>{items.length}</span>
            </div>

            {items.length === 0 ? (
                <div className="empty-state">
                    <span className="empty-state-icon">{emoji}</span>
                    No {label.toLowerCase()} found
                </div>
            ) : (
                items.map((item, i) => (
                    <FeedbackCard key={i} item={item} columnClass={cls} />
                ))
            )}
        </div>
    )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

/**
 * Dashboard — Three-column layout for categorized feedback.
 *
 * Props:
 *   items: FeedbackItem[]  — validated items from the API
 */
export default function Dashboard({ items }) {
    const bugs = items.filter((i) => i.category === 'Bug')
    const features = items.filter((i) => i.category === 'Feature')
    const pains = items.filter((i) => i.category === 'Pain Point')

    return (
        <section>
            <div className="dashboard-header">
                <h2 className="dashboard-title">Categorized Insights</h2>
                <span className="dashboard-count">{items.length} item{items.length !== 1 ? 's' : ''}</span>
            </div>

            <div className="columns">
                <Column category="Bug" items={bugs} />
                <Column category="Feature" items={features} />
                <Column category="Pain Point" items={pains} />
            </div>
        </section>
    )
}
