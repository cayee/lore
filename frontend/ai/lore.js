const userQuery   = document.querySelector("#query");
const hourglass   = document.querySelector("#hourglass");
const chat   = document.querySelector("#chatDiv");
const msgBot   = document.querySelector("#msgBot");
const msgYou   = document.querySelector("#msgYou");
const logQs   = document.querySelector("#LogQuestions");

const debugFields = ["#contextQuestions", "#contextReturnNumber", "#promptPrefix", "#context", "#promptSuffix"]
const cntxtQ = document.querySelector(debugFields[0]);
const cntxtNumber = document.querySelector(debugFields[1]);
const prptPre = document.querySelector(debugFields[2]);
const cntxtField = document.querySelector(debugFields[3]);
const prptSuf = document.querySelector(debugFields[4]);

function insertMsg(node, msg, user=false) {
    let msgNode = node.cloneNode(true);
    msgNode.children[0].children[1].children[0].textContent = msg;
    if (user == true) {
        msgNode.children[0].children[0].children[0].src = "../ico/Icon" + iconOption + ".webp";
    }
    chat.appendChild(msgNode);
    msgNode.scrollIntoView(true);
}

function ask() {
    const question = userQuery.value;
    if (question.length < 1) return;

    hourglass.style.display = "inline";
    insertMsg(msgBot, question, true);

    callAsk(question, function() { //TODO pass whether to save the question
        let answer = `Not ready ${this.status}`;
        if (this.status === 403 || this.status === 401) {
            answer = `Not allowed ${this.status}`;
        } else if (this.status === 200) {
            let response = JSON.parse(this.response);
            answer = response.answers[0].answer;
        }
        else if (this.status === 429) {
            rateLimit();
            answer = "Rate limited";
        }
        hourglass.style.display = "none";
        insertMsg(msgYou, answer);

        if (this.status === 403 || this.status === 401) {
            window.location.href = "index.html";
        }
    });
}

function callAsk(msg, callback){
    let request = new XMLHttpRequest();
    request.open('POST', "AskLore", true);
    request.setRequestHeader('Content-type', 'application/json');
    request.withCredentials = true;
    request.onload = callback;
    request.send(JSON.stringify({"query":msg, "logQuestions": logQs.checked,
        "contextQuestions": cntxtQ.value, "contextReturnNumber": cntxtNumber.value, "promptPrefix": prptPre.value,
        "context": cntxtField.value, "promptSuffix": prptSuf.value}));
}

function rateLimit() {
    //TODO
}

function authenticate(state, scope){
    window.location.href = "index.html";
}

document.getElementById("query").addEventListener("keydown", function(e) {
    // Enter is pressed
    if (e.code == "Enter") {
        document.getElementById("AskQButton").click()
    }
}, false);