const userQuery   = document.querySelector("#query");
const hourglass   = document.querySelector("#hourglass");
const chat   = document.querySelector("#chatDiv");
const msgBot   = document.querySelector("#msgBot");
const msgYou   = document.querySelector("#msgYou");

function insertMsg(node, msg) {
    let msgNode = node.cloneNode(true);
    msgNode.children[0].children[1].children[0].textContent = msg;
    chat.appendChild(msgNode);
    msgNode.scrollIntoView(true);
}

let jwtCognito = null;
function ask() {
    const question = userQuery.value;
    if (question.length < 1) return;

    if (jwtCognito === null) authenticate("ask", "email");    //TODO - fetch from Model select
    else {
        hourglass.style.display = "inline";
        insertMsg(msgBot, question);

        callAsk(question, function() { //TODO pass whether to save the question
            let answer = `Not ready ${this.status}`;
            if (this.status === 403 || this.status === 401) {
                jwtCognito = null;
                answer = `Not allowed ${this.status}`;  //TODO
            } else if (this.status === 200) {
                let response = JSON.parse(this.response);
                answer = response.body;  //TODO
            }
            else if (this.status === 429) {
                rateLimit();
                answer = "Rate limited";
            }

            hourglass.style.display = "none";
            insertMsg(msgYou, answer);
        });
    }
}

const hostName = "https://lore-poc.pwlkrz.people.aws.dev/"
const apiHostName = hostName+"ai/"
function callAsk(msg, callback){
    let request = new XMLHttpRequest();
    request.open('GET', apiHostName+"AskLore", true);
    request.setRequestHeader("X-Authorization", jwtCognito);
    //request.withCredentials = true;
    request.onload = callback;
    request.send();
}

function callToken(code, callback){
    let request = new XMLHttpRequest();
    request.open('GET', apiHostName+"token?code=" + code, true);
    //request.withCredentials = true;
    request.onload = callback;
    request.send();
}

function getToken(code){
    if (code.length !== 36) return;

    callToken(code, function() {
        //TODO - does it save the header?
        if (this.status === 200) {
            let response = JSON.parse(this.response);
            if (response.statusCode === 200) {
                jwtCognito = response.headers.Authorization;
                authOK();
            }
            return;
        }
        jwtCognito = null;
    });
}
function authOK(){
    //TODO rateLimitIcon.style.display = 'none';
    ask();  //ask again - it is the only place where auth is called
}

function rateLimit() {
    //TODO
}

function authenticate(state, scope){
    const appAuthz = "lore-poc";
    const region = "us-east-2";
    const cognitoUrl = "amazoncognito.com";
    const clientId = "38accif6oi0h7knsvjnflgbnti";
    const redirect_uri = hostName + "reload.html";
    window.open(`https://${appAuthz}.auth.${region}.${cognitoUrl}/oauth2/authorize?client_id=${clientId}&response_type=code&scope=${scope}&redirect_uri=${redirect_uri}`);
}
