def lambda_handler(event, context):
    print(f"event: {event}, context: {context}")
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/javascript; charset=utf-8'},
        'body': page
    }

page = """
const userQuery   = document.querySelector("#query");
const hourglass   = document.querySelector("#hourglass");
const chat   = document.querySelector("#chatDiv");
const msgBot   = document.querySelector("#msgBot");
const msgYou   = document.querySelector("#msgYou");

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
            answer = response.answer;
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
    request.open('GET', "AskLore?query="+msg, true);
    request.withCredentials = true;
    request.onload = callback;
    request.send();
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
"""