def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': page
    }

page = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/html" xmlns="http://www.w3.org/1999/html">
<head>
    <title>Lore PoC</title>
    <meta charset="utf-8" />
    <link rel="apple-touch-icon" sizes="180x180" href="../apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../ico/LOL_Icon_Rendered_Hi-Res-NoRing.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../ico/LOL_Icon_Rendered_Hi-Res-NoRing.png">
    <link rel="manifest" href="site.webmanifest">
    <link rel="stylesheet" type="text/css" href="../lore.css">

    <script>
        iconOption = 1
        function changeIcon(o)
        {
            chosenOption = o.value;
            if (chosenOption == "Blue minion bruiser")
            {   iconOption = 1  }
            if (chosenOption == "Penguin toss")
            {   iconOption = 2  }
            if (chosenOption == "Demacia crest")
            {   iconOption = 3  }
            if (chosenOption == "PROJECT: Jhin")
            {   iconOption = 4  }
            if (chosenOption == "Blazing feathers")
            {   iconOption = 5  }
            console.log(iconOption)
        }
    </script>
</head>
<body>
    <h2 id="MainH">League of Legends Loremaster v0.1</h2>
<div>
    <p id="QuestionP">
        <input type="checkbox" checked="true"/>
            Save my Q&A for future training purposes
    </p>
</div>
<div>
    <span style="margin-right: 5px">Choose your icon: </span>
    <select id="iconSelect" onchange="changeIcon(this)">
        <option>Blue minion bruiser</option>
        <option>Penguin toss</option>
        <option>Demacia crest</option>
        <option>PROJECT: Jhin</option>
        <option>Blazing feathers</option>
    </select>
</div>
<br>
<div>
    <span style="margin-right: 5px">Choose your model: </span>
    <select id="modelSelect" onchange="changeModel(this)">
        <option>Prime</option>
    </select>
</div>
<br>
<div id="chatDiv" style="width: 300px; height: 300px; max-height: 300px; overflow-y: scroll">
    <div hidden>
    <div class="message" id="msgBot">
        <div class="message__outer" style="flex-direction: row-reverse">
            <div class="message__avatar">
                <img class="avatar" src="../ico/Icon1.webp" width="28" height="28">
            </div>
            <div class="message__inner" style="flex-direction: row-reverse">
                <div class="message__bubble" style="background-color: #f0e8e8; color: rgb(30,30,33);">Hello!</div>
            </div>
            <div class="message__status"></div>
        </div>
    </div>
    <div class="message" id="msgYou">
        <div class="message__outer" style="flex-direction: row">
            <div class="message__avatar">
                <img class="avatar" src="../ico/LoL_Icon_Flat_GOLD.png" width="28" height="28">
            </div>
            <div class="message__inner">
                <div class="message__bubble" style="background-color: rgb(30, 30, 33);">Veeery loong text about anything but nothing else!</div>
            </div>
            <div class="message__status"></div>
        </div>
    </div>
    
    </div>
</div>

<div style="text-align: left;">
    <input type="text" id="query" placeholder="Message..."></input>
    <button id="AskQButton" onclick="ask()"><img src="../ico/send_message.png" style="height: 30px; width: 30px; vertical-align: middle;"/></button>
    <img id="hourglass" src="../ico/zhonyas_old.webp" width="16" height="16" style="display: none">
</div>

<script src="lore.js"></script>
</body>
</html>

"""