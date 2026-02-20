import { Conversation } from '../lib/api'

interface ConversationListProps {
  conversations: Conversation[]
}

export default function ConversationList({ conversations }: ConversationListProps) {
  if (conversations.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-secondary)' }}>No conversations yet</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {conversations.map((conversation) => (
        <div
          key={conversation.id}
          className="card"
          style={{
            borderLeft: `4px solid ${conversation.direction === 'inbound' ? 'var(--info)' : 'var(--success)'}`,
            background: conversation.direction === 'inbound' ? 'var(--bg-secondary)' : 'var(--bg-tertiary)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
              {conversation.direction === 'inbound' ? '← Inbound' : '→ Outbound'}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
              {new Date(conversation.created_at).toLocaleString()}
            </span>
          </div>
          
          <div style={{ fontSize: '0.875rem', marginBottom: '5px', color: 'var(--text-secondary)' }}>
            <strong>Type:</strong> {conversation.message_type}
          </div>
          
          {conversation.content && (
            <div style={{ fontSize: '0.875rem', marginTop: '10px', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
              {conversation.content}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
