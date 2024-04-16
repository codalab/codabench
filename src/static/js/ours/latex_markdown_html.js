// Function to render Markdown,  HTML and Latex and return updated content
function renderMarkdownWithLatex(content) {
  if(content === null){
    return []
  }
  const parsedHtml = new DOMParser().parseFromString(marked(content), "text/html")

  const traverseAndRenderLatex = (node) => {
    if (node.nodeType === Node.ELEMENT_NODE) {
      const latexPattern = /\$\$([\s\S]*?)\$\$|\$([^\$\n]*?)\$/g
      const hasLatex = latexPattern.test(node.textContent)
      if (hasLatex) {
        const tempDiv = document.createElement('div')
        tempDiv.innerHTML = node.innerHTML.replace(latexPattern, (_, formula1, formula2) => {
          const formula = formula1 || formula2
          const decodedFormula = formula.replace(/&lt;/g, '<').replace(/&gt;/g, '>')
          return katex.renderToString(decodedFormula, { throwOnError: false })
        });
        node.innerHTML = tempDiv.innerHTML
      }
    }

    node.childNodes.forEach(traverseAndRenderLatex)
  };

  traverseAndRenderLatex(parsedHtml.body)

  return parsedHtml.body.childNodes
}