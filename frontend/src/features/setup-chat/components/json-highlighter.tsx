import { useMemo } from 'react'

const escapeHtml = (unsafe: string) => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function JsonHighlighter({ data }: { data: unknown }) {
  const html = useMemo(() => {
    let jsonStr = ''
    try {
      jsonStr = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
    } catch {
      jsonStr = String(data)
    }

    // Match JSON tokens BEFORE escaping HTML
    const jsonRegex = /("(?:\\.|[^"\\])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g
    
    let lastIndex = 0;
    let result = '';
    
    jsonStr.replace(jsonRegex, (match, ...args) => {
      const offset = args[args.length - 2];
      
      // Escape anything between the last token and this one (e.g. spaces, brackets, braces)
      result += escapeHtml(jsonStr.substring(lastIndex, offset));
      lastIndex = offset + match.length;
      
      let color = '#abb2bf';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          color = '#e06c75'; // Key
        } else {
          color = '#98c379'; // String
          // Unescape newlines and tabs to make long text visually readable
          match = match.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
        }
      } else if (/true|false/.test(match)) {
        color = '#d19a66';
      } else if (/null/.test(match)) {
        color = '#d19a66';
      } else {
        color = '#d19a66';
      }
      
      result += `<span style="color: ${color}">${escapeHtml(match)}</span>`;
      return match;
    });
    
    result += escapeHtml(jsonStr.substring(lastIndex));
    return result;
  }, [data])

  return (
    <pre 
      dangerouslySetInnerHTML={{ __html: html }} 
      style={{ 
        whiteSpace: 'pre-wrap', 
        margin: 0, 
        padding: '12px', 
        fontSize: '0.85em', 
        fontFamily: 'monospace', 
        wordBreak: 'break-word', 
        color: '#abb2bf', 
        background: '#282c34', 
        borderRadius: '6px' 
      }} 
    />
  )
}
