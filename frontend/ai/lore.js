const logQs   = document.querySelector("#LogQuestions");
const sendAll   = document.querySelector("#SendAll");

const userQueryVi   = document.querySelector("#query2");
const hourglassVi   = document.querySelector("#hourglass2");
const chatVi   = document.querySelector("#chatDiv2");
const msgBotVi   = document.querySelector("#msgBot2");
const msgYouVi   = document.querySelector("#msgYou2");
const locationVi   = document.querySelector("#LocationVi");
const storyBackground   = document.querySelector("#StoryBackground");

const debugFields = ["#contextQuestions", "#contextReturnNumber", "#promptPrefix", "#context", "#promptSuffix"]
const cntxtQ = document.querySelector(debugFields[0]);
const cntxtNumber = document.querySelector(debugFields[1]);
const prptPre = document.querySelector(debugFields[2]);
const cntxtField = document.querySelector(debugFields[3]);
const prptSuf = document.querySelector(debugFields[4]);

function insertMsg(node, msg, chat, user=false) {
    let msgNode = node.cloneNode(true);
    msgNode.children[0].children[1].children[0].textContent = msg;
    if (user === true) {
        msgNode.children[0].children[0].children[0].src = "../ico/Icon" + iconOption + ".webp";
    }
    chat.appendChild(msgNode);
    msgNode.scrollIntoView(true);
}

function postAsk(api, data, callback) {
    let request = new XMLHttpRequest();
    request.open('POST', api, true);
    request.setRequestHeader('Content-type', 'application/json');
    request.withCredentials = true;
    request.onload = callback;
    request.send(JSON.stringify(data));
}

function ask(suff) {
    const question = document.querySelector("#query"+suff).value;
    if (question.length < 1) return;

    const chats = sendAll.checked ? ['', '-2', '-3']: [suff];
    const loreTypes = ["Default", "First", "Second"];

    for (suffId in chats) {
        suff = chats[suffId];

        let hourglass = document.querySelector("#hourglass" + suff);
        let msgBot = document.querySelector("#msgBot" + suff);
        let msgYou = document.querySelector("#msgYou" + suff);
        let chat = document.querySelector("#chatDiv" + suff);
        hourglass.style.display = "inline";
        insertMsg(msgBot, question, chat, true);

        postAsk("AskLore", {
                "query": question, "logQuestions": logQs.checked,
                "contextQuestions": cntxtQ.value, "contextReturnNumber": cntxtNumber.value, "promptPrefix": prptPre.value,
                "context": cntxtField.value, "promptSuffix": prptSuf.value,
                "sessId": "Lore" + suff, "loreType": loreTypes[suffId]
            },
            function () {
                let answer = `Not ready ${this.status}`;
                if (this.status === 403 || this.status === 401) {
                    answer = `Not allowed ${this.status}`;
                } else if (this.status === 200) {
                    let response = JSON.parse(this.response);
                    answer = response.answers[0].answer;
                } else if (this.status === 429) {
                    answer = "Rate limited";
                }
                hourglass.style.display = "none";
                insertMsg(msgYou, answer, chat);

                if (this.status === 403 || this.status === 401) {
                    window.location.href = "index.html";
                }
            });
    };
}

function handleViResponse() {
    let answer = `Not ready ${this.status}`;
    let storyLocation = locationVi.textContent.substring(10);   // "Location: ".length
    if (this.status === 403 || this.status === 401) {
        answer = `Not allowed ${this.status}`;
    } else if (this.status === 200) {
        let response = JSON.parse(this.response);
        answer = response.answers[0].answer;
        storyLocation = response.answers[0].location
    }
    else if (this.status === 429) {
        answer = "Rate limited";
    }
    hourglassVi.style.display = "none";
    insertMsg(msgYouVi, answer, chatVi);
    locationVi.textContent = "Location: " + storyLocation
    if (storyLocation === "Piltover plaza") {
        storyBackground.src = "../img/Piltover.jpg"
    } else if (storyLocation === "Ecliptic Vaults") {
        storyBackground.src = "../img/Vaults.jpg"
    } else if (storyLocation === "the Lanes") {
        storyBackground.src = "../img/Zaun.jpg"
    }

    if (this.status === 403 || this.status === 401) {
        window.location.href = "index.html";
    }
}
function ask2() {
    const question = userQueryVi.value;
    if (question.length < 1) return;

    hourglassVi.style.display = "inline";
    insertMsg(msgBotVi, question, chatVi);

    postAsk("AskVi", {"query": question, "logQuestions": logQs.checked, "resetChat": false, "sessId": "Vi"}, handleViResponse)
}

function askViAgain() {
    hourglassVi.style.display = "inline";
    postAsk("AskLast", {"sessId": "Vi"}, handleViResponse)
}

function actOnEnter(but) {
    document.getElementById("query").addEventListener("keydown", function(e) {
        if (e.code === "Enter") document.getElementById(but).click()
    }, false);
}

actOnEnter("AskQButton")
actOnEnter("AskQButton2")
actOnEnter("AskQButton-2")
actOnEnter("AskQButton-3")
