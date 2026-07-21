import { useEffect, useState, useRef } from 'react'
import { adminApi } from '../api/admin-api'
import type { ToolCustomizationRuleCreate, ToolCustomizationRuleRead } from '../api/admin-api'
import { Button } from '../../../shared/components/button'
import { DataTable } from '../../../shared/components/design-system'
import { Drawer } from '../../../shared/components/drawer'

export function ChatCustomizationPanel() {
  const [rules, setRules] = useState<ToolCustomizationRuleRead[]>([])
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<ToolCustomizationRuleRead | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Form states
  const [prefix, setPrefix] = useState('')
  const [iconFile, setIconFile] = useState<File | null>(null)
  const [iconUrl, setIconUrl] = useState('')
  const [previewUrl, setPreviewUrl] = useState('')
  const [requestColor, setRequestColor] = useState('')
  const [responseColor, setResponseColor] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!iconFile) {
      setPreviewUrl('')
      return
    }
    const url = URL.createObjectURL(iconFile)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [iconFile])

  const loadRules = async () => {
    try {
      const data = await adminApi.toolCustomizations()
      setRules(data)
    } catch (e: any) {
      setError(e.message || 'Failed to load rules')
    }
  }

  useEffect(() => {
    void loadRules()
  }, [])

  const handleOpenDrawer = (rule?: ToolCustomizationRuleRead) => {
    if (rule) {
      setEditingRule(rule)
      setPrefix(rule.tool_name_prefix)
      setIconUrl(rule.icon_url)
      setRequestColor(rule.request_color || '')
      setResponseColor(rule.response_color || '')
    } else {
      setEditingRule(null)
      setPrefix('')
      setIconUrl('')
      setRequestColor('')
      setResponseColor('')
    }
    setIconFile(null)
    setError(null)
    setIsDrawerOpen(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const payload: ToolCustomizationRuleCreate = {
        tool_name_prefix: prefix,
        icon_url: iconUrl || undefined,
        request_color: requestColor || undefined,
        response_color: responseColor || undefined
      }

      let savedRule
      if (editingRule) {
        savedRule = await adminApi.updateToolCustomization(editingRule.id, payload)
      } else {
        savedRule = await adminApi.createToolCustomization(payload)
      }
      
      if (iconFile) {
        await adminApi.uploadIcon(savedRule.id, iconFile)
      }

      setIsDrawerOpen(false)
      void loadRules()
    } catch (err: any) {
      setError(err.message || 'Failed to save rule')
    }
  }

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this rule?')) {
      try {
        await adminApi.deleteToolCustomization(id)
        void loadRules()
      } catch (e: any) {
        setError(e.message || 'Failed to delete rule')
      }
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3>Tool Customization Rules</h3>
        <Button onClick={() => handleOpenDrawer()}>Add Rule</Button>
      </div>

      {error && <p role="alert" className="error-banner">{error}</p>}

      <DataTable
        headers={['Prefix', 'Icon', 'Request Color', 'Response Color', 'Actions']}
        empty={<p className="muted">No customization rules found.</p>}
      >
        {rules.map((rule) => (
          <tr key={rule.id}>
            <td>{rule.tool_name_prefix}</td>
            <td>
              {rule.icon_url ? (
                <img 
                  src={rule.icon_url} 
                  alt="icon" 
                  style={{ width: 24, height: 24 }} 
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    if (e.currentTarget.nextElementSibling) {
                      e.currentTarget.nextElementSibling.removeAttribute('hidden');
                    }
                  }}
                />
              ) : null}
              <span hidden={!!rule.icon_url} style={{ fontSize: '1.2em' }}>🛠️</span>
            </td>
            <td>
              {rule.request_color && (
                <span style={{ display: 'inline-block', width: 16, height: 16, backgroundColor: rule.request_color, marginRight: 8, verticalAlign: 'middle' }}></span>
              )}
              {rule.request_color || 'Default'}
            </td>
            <td>
              {rule.response_color && (
                <span style={{ display: 'inline-block', width: 16, height: 16, backgroundColor: rule.response_color, marginRight: 8, verticalAlign: 'middle' }}></span>
              )}
              {rule.response_color || 'Default'}
            </td>
            <td className="row-actions">
              <Button variant="ghost" onClick={() => handleOpenDrawer(rule)}>Edit</Button>
              <Button variant="danger" onClick={() => handleDelete(rule.id)}>Delete</Button>
            </td>
          </tr>
        ))}
      </DataTable>

      <Drawer
        open={isDrawerOpen}
        onOpenChange={setIsDrawerOpen}
        title={editingRule ? 'Edit Rule' : 'New Rule'}
      >
        <form onSubmit={handleSave} className="stack-gap" style={{ padding: '16px 0' }}>
          <div className="form-field">
            <label>Tool Name Prefix</label>
            <input
              type="text"
              required
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              className="input-field"
              placeholder="e.g. search_"
            />
          </div>
          
          <div className="form-field">
            <label>Icon</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              {(iconFile || iconUrl) ? (
                <div style={{ position: 'relative', width: 64, height: 64, border: '1px solid var(--border-color, #ccc)', borderRadius: '8px', overflow: 'hidden', backgroundColor: 'var(--bg-muted, #f3f4f6)' }}>
                  <img
                    src={iconFile ? (previewUrl || undefined) : (iconUrl || undefined)}
                    alt="Icon preview"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setIconFile(null)
                      setIconUrl('')
                      if (fileInputRef.current) {
                        fileInputRef.current.value = ''
                      }
                    }}
                    style={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                      background: 'rgba(0,0,0,0.6)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '50%',
                      width: 20,
                      height: 20,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      padding: 0
                    }}
                    title="Remove icon"
                  >
                    ✕
                  </button>
                </div>
              ) : null}
              
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={(e) => setIconFile(e.target.files?.[0] || null)}
                  style={{ display: 'none' }}
                />
                <Button 
                  type="button" 
                  variant="ghost" 
                  onClick={() => fileInputRef.current?.click()}
                >
                  Upload Icon
                </Button>
              </div>
            </div>
          </div>

          <div className="form-field">
            <label>Request Styling Color (Optional hex)</label>
            <input
              type="color"
              value={requestColor || '#000000'}
              onChange={(e) => setRequestColor(e.target.value)}
              className="input-field"
            />
            <button type="button" onClick={() => setRequestColor('')} className="button button--ghost" style={{ marginTop: 4 }}>Clear Color</button>
          </div>

          <div className="form-field">
            <label>Response Styling Color (Optional hex)</label>
            <input
              type="color"
              value={responseColor || '#000000'}
              onChange={(e) => setResponseColor(e.target.value)}
              className="input-field"
            />
            <button type="button" onClick={() => setResponseColor('')} className="button button--ghost" style={{ marginTop: 4 }}>Clear Color</button>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
            <Button type="submit">Save</Button>
            <Button type="button" variant="ghost" onClick={() => setIsDrawerOpen(false)}>Cancel</Button>
          </div>
        </form>
      </Drawer>
    </div>
  )
}
