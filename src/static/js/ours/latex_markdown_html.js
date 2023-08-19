// // Function to render Markdown and HTML content and return updated content
// function renderMarkdownAndHTML(content) {
//     const parsedHtml = new DOMParser().parseFromString(marked(content), "text/html");
//     return parsedHtml.body.childNodes;
//   }


// // Function to render LaTeX formulas using KaTeX and return updated content
// function renderLatexInContent(content) {
//     const parsedHtml = new DOMParser().parseFromString(content, "text/html");
//     const traverseAndRender = (node) => {
//       if (node.nodeType === Node.ELEMENT_NODE) {
//         const latexPattern = /\$\$([\s\S]*?)\$\$|\$([^\$\n]*?)\$/g;
//         const hasLatex = latexPattern.test(node.textContent);
//         if (hasLatex) {
//           const tempDiv = document.createElement('div');
//           tempDiv.innerHTML = node.innerHTML.replace(latexPattern, (_, formula1, formula2) => {
//             const formula = formula1 || formula2;
//             return katex.renderToString(formula, { throwOnError: false });
//           });
//           node.innerHTML = tempDiv.innerHTML;
//         }
//       }
//       node.childNodes.forEach(traverseAndRender);
//     };
//     traverseAndRender(parsedHtml.body);
//     return parsedHtml.body.innerHTML;
//   }



function renderMarkdownWithLatex(content) {
    const parsedHtml = new DOMParser().parseFromString(marked(content), "text/html");
  
    const traverseAndRenderLatex = (node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const latexPattern = /\$\$([\s\S]*?)\$\$|\$([^\$\n]*?)\$/g;
        const hasLatex = latexPattern.test(node.textContent);
        if (hasLatex) {
          const tempDiv = document.createElement('div');
          tempDiv.innerHTML = node.innerHTML.replace(latexPattern, (_, formula1, formula2) => {
            const formula = formula1 || formula2;
            return katex.renderToString(formula, { throwOnError: false });
          });
          node.innerHTML = tempDiv.innerHTML;
        }
      }
  
      node.childNodes.forEach(traverseAndRenderLatex);
    };
  
    traverseAndRenderLatex(parsedHtml.body);
  
    return parsedHtml.body.childNodes;
}