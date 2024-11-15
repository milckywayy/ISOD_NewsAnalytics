
function copyToClipboard() {
    const codeElement = document.getElementById("analytics-tag");
    const code = codeElement.textContent;

    navigator.clipboard.writeText(code).then(() => {
        alert("Code copied successfully!!");
    }).catch(err => {
        console.error("Error: ", err);
    });
}
