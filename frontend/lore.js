const userQuery   = document.querySelector("#query");
const hourglass   = document.querySelector("#hourglass");
const chatTable   = document.querySelector("#chat");
const chatDiv   = document.querySelector("#chatDiv");
const msgBot   = document.querySelector("#msgBot");
const msgYou   = document.querySelector("#msgYou");

const COL_BOT = 0;
const COL_MSG = 1;
const COL_YOU = 2;

const botMsgStyle = "";
const youMsgStyle = "";
function insertRow(tbl, lft, msg, rgt) {

    let body = tbl.children[0];
    let row = body.children[0].cloneNode(true);
    row.children[COL_MSG].textContent = msg;
    if (lft === null) { // question
        row.children[COL_BOT].textContent = "";
        row.children[COL_YOU].textContent = rgt;
        row.style = youMsgStyle;
    }
    else {
        row.children[COL_BOT].textContent = lft;
        row.children[COL_YOU].textContent = "";
        row.style = botMsgStyle;
    }
    body.appendChild(row);
}
function ask() {
    hourglass.style.display = "inline";
    const question = userQuery.value;
    insertRow(chatTable, null, question, "me");
    //TODO - ask model
    answer = "Not ready";
    insertRow(chatTable, "bot", answer, null);
    hourglass.style.display = "none";
}