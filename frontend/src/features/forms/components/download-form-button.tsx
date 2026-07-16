import { useState } from 'react'

import { Button } from '../../../shared/components/button'
import { formsApi, type FormTemplateKey } from '../api/forms-api'
import { downloadTextFile } from '../lib/download-markdown'

export function DownloadFormButton({ formKey }: { formKey: FormTemplateKey }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const download = async () => {
    setLoading(true)
    setError(null)
    try {
      const template = await formsApi.downloadTemplate(formKey)
      downloadTextFile(template.filename, template.content)
    } catch {
      setError('Could not download the offline form.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <span className="inline-actions">
      <Button type="button" variant="ghost" disabled={loading} onClick={() => void download()}>
        {loading ? 'Downloading…' : 'Download'}
      </Button>
      {error ? <small role="alert">{error}</small> : null}
    </span>
  )
}
