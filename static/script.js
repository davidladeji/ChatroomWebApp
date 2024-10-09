let timeoutID;
let timeoutIDRoomExists;
let timeout = 1000;

let roomExists = true;

function setup() {
    // Add event listener to submit button
    document.getElementById("submit-btn").addEventListener("click", makeMessage);
    timeoutID = window.setTimeout(poller, timeout);
    timeoutIDRoomExists = window.setTimeout(checkRoomExists, timeout);
}

function makeMessage() {
    console.log("Sending POST request");
	const message = document.getElementById("usermsg").value;
    let userdiv = document.getElementById("user-info");
    var index = userdiv.textContent;

    fetch(`/post_message/${index}`, {
        method: "post",
        headers: { "Content-type": "application/x-www-form-urlencoded" },
        body: `message=${message}`
    })
    .then((response) => {
        return response.json();
    })
    .then((result) => {
        updateChatbox(result);
        clearInput();
    })
    .catch((error) => {
        console.log(error);
        console.log("Error posting new items!");
    });

}

function updateChatbox(result) {
    console.log("Updating the table");
    const userMsgDiv = document.getElementById("newMsg-div");
    
    const children = userMsgDiv.children;

    // Delete all new messages
    while (children.length > 0){
        userMsgDiv.removeChild(children[0]);
    }

    // Create new divs for all new messages and append them
    for (let i=0; i<result.length; i++){

        let msgDiv = document.createElement("div");
        let str = result[i][0];
        const username = str.charAt(0).toUpperCase() + str.slice(1);
        let newMsg = document.createTextNode(username + ": " + result[i][1]);
        msgDiv.appendChild(newMsg);
        userMsgDiv.appendChild(msgDiv);
    }

    
    timeoutID = window.setTimeout(poller, timeout);
}

function poller() {
	console.log("Polling for new messages");
    let userdiv = document.getElementById("user-info");
    var index = userdiv.textContent;
	fetch(`/messages/${index}`)
		.then((response) => {
			return response.json();
		})
		.then(updateChatbox)
		.catch(() => {
			console.log("Error fetching items!");
		});
}

function checkRoomExists() {
	console.log("Polling for room being deleted");
    let roomdiv = document.getElementById("room-info");
    var index = roomdiv.textContent;
	fetch(`/get_room_exists/${index}`)
		.then((response) => {
			return response.json();
		})
        .then((result) => {
            handleRoomExists(result)
        })
		.catch(() => {
			console.log("Error fetching items!");
		});
}

function handleRoomExists(result) {
    if (result == 0) {
        window.clearTimeout();
        const container = document.getElementById("container");
        const children = container.children;

        // Delete everything on this page
        while (children.length > 0){
            container.removeChild(children[0]);
        }

        let msgDiv = document.createElement("div");
        let str = document.createTextNode("This room just got deleted by its creator. Please refresh this page");

        let breakElement = document.createElement("br");
        let str2 = document.createTextNode("Please refresh this page");

        msgDiv.id = "bigger-alert";
        msgDiv.appendChild(str);
        msgDiv.appendChild(breakElement);
        msgDiv.appendChild(str2);
        container.appendChild(msgDiv);
    }

    else {
        timeoutIDRoomExists = window.setTimeout(checkRoomExists, timeout);
    }
    
}

function clearInput() {
	console.log("Clearing input");
	document.getElementById("usermsg").value = "";
}


window.addEventListener("load", setup);