function convertCustomTagsToHtml(input) {
    // Сопоставление пользовательских тегов с HTML/стилями
    const tagMap = {
        red: (content) => `<span style="color:red">${content}</span>`,
        green: (content) => `<span style="color:green">${content}</span>`,
        yellow: (content) => `<span style="color:yellow">${content}</span>`,
        white: (content) => `<span style="color:white">${content}</span>`,
        magenta: (content) => `<span style="color:magenta">${content}</span>`,
        blue: (content) => `<span style="color:blue">${content}</span>`,
        cyan: (content) => `<span style="color:cyan">${content}</span>`,
        b: (content) => `<b>${content}</b>`,
        d: (content) => `<span style="opacity:0.6">${content}</span>`,
        u: (content) => `<u>${content}</u>`,
    };

    // Экранирование HTML в текстовых узлах
    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    // Парсинг строки в дерево узлов
    function parseToTree(text) {
        const root = { type: 'root', children: [] };
        const stack = [root];
        let currentText = '';
        let i = 0;

        while (i < text.length) {
            if (text[i] === '<') {
                // Обработка закрывающего тега
                if (text[i + 1] === '/') {
                    const tagEnd = text.indexOf('>', i + 2);
                    if (tagEnd === -1) {
                        currentText += text[i];
                        i++;
                        continue;
                    }

                    const tagName = text.substring(i + 2, tagEnd);
                    if (stack.length > 1 && stack[stack.length - 1].tag === tagName) {
                        if (currentText) {
                            stack[stack.length - 1].children.push({
                                type: 'text',
                                content: currentText
                            });
                            currentText = '';
                        }
                        stack.pop();
                        i = tagEnd + 1;
                    } else {
                        currentText += text.substring(i, tagEnd + 1);
                        i = tagEnd + 1;
                    }
                }
                // Обработка открывающего тега
                else {
                    const tagEnd = text.indexOf('>', i + 1);
                    if (tagEnd === -1) {
                        currentText += text[i];
                        i++;
                        continue;
                    }

                    const tagName = text.substring(i + 1, tagEnd);
                    if (tagMap[tagName]) {
                        if (currentText) {
                            stack[stack.length - 1].children.push({
                                type: 'text',
                                content: currentText
                            });
                            currentText = '';
                        }

                        const node = {
                            type: 'tag',
                            tag: tagName,
                            children: []
                        };
                        stack[stack.length - 1].children.push(node);
                        stack.push(node);
                        i = tagEnd + 1;
                    } else {
                        currentText += text.substring(i, tagEnd + 1);
                        i = tagEnd + 1;
                    }
                }
            } else {
                currentText += text[i];
                i++;
            }
        }

        if (currentText) {
            stack[stack.length - 1].children.push({
                type: 'text',
                content: currentText
            });
        }

        return root;
    }

    // Генерация HTML из дерева
    function generateHtml(node) {
        if (node.type === 'text') {
            return escapeHtml(node.content);
        }

        if (node.type === 'root') {
            return node.children.map(generateHtml).join('');
        }

        if (node.type === 'tag') {
            const innerHtml = node.children.map(generateHtml).join('');
            return tagMap[node.tag](innerHtml);
        }

        return '';
    }

    const rootNode = parseToTree(input);

    let out = generateHtml(rootNode);
    out = '<span class="gray-text">'+ out +'</span>'
    console.log(input + "\n =>>> \n"+ out )
    console.log("-")
    return out
}