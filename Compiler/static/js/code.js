const content = document.querySelector(".content");

const elementTypes = [
  "header",
  "main",
  "footer",
  "p",
  "section",
  "h1",
  "ul",
  "a",
  "li",
  "h2",
  "nav"
];

const numberOfTypes = elementTypes.length;

for (let i = 0; i < numberOfTypes; i++) {
  let elements = content.getElementsByTagName(elementTypes[i]);
  for (let j = 0; j < elements.length; j++) {
    let selectedElement = elements[j];
    let tagName = selectedElement.tagName;
    let openingTagText;
    if (selectedElement.tagName == "A") {
      let URL = selectedElement.getAttribute("href");
       openingTagText =
        '<span class="tag">&lt;a </span><span class="attribute-name"> href</span>=<span class="attribute-value">"' +
        URL +
        '"</span><span class="tag">&gt;</span>';
    } else if (selectedElement.tagName === "SECTION") {
      let id = selectedElement.getAttribute("id");
       openingTagText =
        '<span class="tag">&lt;section </span><span class="attribute-name"> id</span>=<span class="attribute-value">"' +
        id +
        '"</span><span class="tag">&gt;</span>';
    } else {
       openingTagText = "&lt;" + tagName + "&gt;";
    }
    let openingTag = document.createElement("span");
    openingTag.innerHTML = openingTagText;
    selectedElement.prepend(openingTag);
    openingTag.setAttribute("aria-hidden", "true");
    openingTag.setAttribute("class", "tag");

    let closingTagText = "&lt;/" + tagName + "&gt;";
    let closingTag = document.createElement("span");
    closingTag.innerHTML = closingTagText;
    selectedElement.append(closingTag);
    closingTag.setAttribute("class", "tag");
    closingTag.setAttribute("aria-hidden", "true");
  }
}

const close = document.getElementsByClassName("close")[0];
close.addEventListener("click", function closewindow() {
  const window = document.getElementsByClassName("vscode-window")[0];
  window.setAttribute("style", "display: none");
});

const open = document.getElementsByClassName("open")[0];
open.addEventListener("click", function openwindow() {
  const window = document.getElementsByClassName("vscode-window")[0];
  window.setAttribute("style", "display: block");
});