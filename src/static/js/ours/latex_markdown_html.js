// Function to render Markdown content that may include:
// - Code blocks (```...```)
// - Inline and block LaTeX ($...$ or $$...$$)
// - HTML
// The function returns an array of DOM nodes generated from the fully rendered and processed content.
function renderMarkdownWithLatex(content) {
  if (!content) return [] // Return empty if content is null or empty

  // ---------------------------------------------------------
  // Step 1: Extract and temporarily replace all code blocks
  // ---------------------------------------------------------

  // Regex to match code blocks in Markdown: ```[language]\n[code]```
  const codeBlockPattern = /```(\w*)\n([\s\S]*?)```/g
  const codeBlocks = [] // Store original code blocks and their tokens
  let codeIndex = 0     // Counter to generate unique tokens for code blocks

  // Replace each code block with a unique token and store the original
  const contentWithoutCode = content.replace(codeBlockPattern, (_, lang, code) => {
    const token = `%%CODE_BLOCK_${codeIndex++}%%`
    codeBlocks.push({ token, lang, code }) // Store the token and the original code
    return token // Replace the block with its token in the text
  })

  // ---------------------------------------------------------
  // Step 2: Extract and replace LaTeX expressions with placeholders
  // ---------------------------------------------------------

  // Regex to match inline ($...$) and block ($$...$$) LaTeX formulas
  const latexPattern = /\$\$([\s\S]+?)\$\$|\$([^\$\n]+?)\$/g
  const latexBlocks = [] // Store rendered LaTeX HTML and their tokens
  let latexIndex = 0     // Counter for LaTeX token IDs

  // Replace LaTeX expressions with unique tokens and store rendered HTML
  const contentWithLatexPlaceholders = contentWithoutCode.replace(latexPattern, (_, block, inline) => {
    const formula = block || inline          // Pick block or inline formula content
    const displayMode = !!block              // Use displayMode for block ($$...$$)
    let rendered                             // Store the rendered HTML from KaTeX

    try {
      // Render LaTeX to HTML using KaTeX
      rendered = katex.renderToString(formula, {
        throwOnError: false,
        displayMode,
      })
    } catch (e) {
      console.error("KaTeX error:", e)
      rendered = `<code>${formula}</code>` // If render fails, fallback to raw code
    }

    const token = `%%LATEX_BLOCK_${latexIndex++}%%`
    latexBlocks.push({ token, rendered }) // Store the token and rendered HTML
    return token // Replace formula with its token in the text
  })

  // ---------------------------------------------------------
  // Step 3: Convert Markdown to HTML
  // ---------------------------------------------------------

  // Run the Markdown parser on the content (now safe with all code and LaTeX replaced by tokens)
  let html = marked(contentWithLatexPlaceholders)

  // ---------------------------------------------------------
  // Step 4: Restore rendered LaTeX blocks into the HTML
  // ---------------------------------------------------------

  // Replace each LaTeX token with the rendered KaTeX HTML
  for (const { token, rendered } of latexBlocks) {
    html = html.replace(token, rendered)
  }

  // ---------------------------------------------------------
  // Step 5: Restore escaped code blocks back into the HTML
  // ---------------------------------------------------------

  // Replace each code block token with HTML-safe <pre><code> block
  for (const { token, code, lang } of codeBlocks) {
    const safeCode = escapeHtml(code) // Escape HTML-sensitive characters inside code
    html = html.replace(token, `<pre><code class="language-${lang}">${safeCode}</code></pre>`)
  }


  // ---------------------------------------------------------
  // Step 6: Convert final HTML string into DOM nodes and return
  // ---------------------------------------------------------

  // Parse the final HTML string into actual DOM nodes
  const parsedHtml = new DOMParser().parseFromString(html, "text/html")

  // Return child nodes from the parsed HTML body
  return parsedHtml.body.childNodes
}

// Utility function to escape HTML special characters inside code blocks
function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")   // escape ampersands
    .replace(/</g, "&lt;")    // escape <
    .replace(/>/g, "&gt;")    // escape >
    .replace(/"/g, "&quot;")  // escape double quotes
    .replace(/'/g, "&#39;")   // escape single quotes
}

