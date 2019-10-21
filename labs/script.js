(function() {
    // md-content__inner
    const replaceOnDocument = (pattern, string, {target = document.body} = {}) => {
        // Handle `string` — see the last section
        [
            target,
            ...target.querySelectorAll("*:not(script):not(noscript):not(style)")
        ].forEach(({childNodes: [...nodes]}) => nodes
            .filter(({nodeType}) => nodeType === document.TEXT_NODE)
            .forEach((textNode) => textNode.textContent = textNode.textContent.replace(pattern, string)));
    };
    replaceOnDocument(/\[USER\]/g, "lbischof", document.getElementsByClassName("md-content__inner")[0]);
})();
