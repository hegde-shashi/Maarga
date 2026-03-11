chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

    console.log("Message received:", request);

    if (request.action === "extract") {

        const data = {
            url: window.location.href,
            title: document.title,
            text: document.body.innerText
        };

        console.log("Sending page data");

        sendResponse(data);
    }

});