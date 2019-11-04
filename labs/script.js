function createUsernamePrompt() {
    var modal = document.createElement('div')
    modal.setAttribute('id', 'usernamePrompt')

    // TODO: add button to skip prompt
    modal.innerHTML = [
        '<p>Please enter your Techlab Username:</p>',
        '<input id="usernamePromptInput" type="text"></input>',
        '<button id="usernamePromptButton">Set Username</button>'
    ].join('\n');
    document.body.appendChild(modal)

    let btn = document.getElementById('usernamePromptButton')
    let input = document.getElementById('usernamePromptInput')
    btn.addEventListener('click', function(e) {
        console.log('clicked')
        localStorage.setItem("username", input.value)
        // TODO: close modal
    })
}

(function() {
    console.log(localStorage.getItem("username"))

    let username = localStorage.getItem("username")
    if (!username) {
        console.log("Please set a username")
        createUsernamePrompt()
    }

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
    replaceOnDocument(/\[USER\]/g, username, document.getElementsByClassName("md-content__inner")[0]);
})();
