const API_BASE =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost"
        ? "http://127.0.0.1:8001"
        : "https://music-downloader-pupp.onrender.com";


// =========================================================
// ELEMENTS
// =========================================================

const spotifyUrl = document.getElementById("spotifyUrl");
const pasteButton = document.getElementById("pasteButton");
const analyzeButton = document.getElementById("analyzeButton");
const inputNote = document.getElementById("inputNote");

const results = document.getElementById("results");
const closeResults = document.getElementById("closeResults");

const trackThumbnail = document.getElementById("trackThumbnail");
const trackTitle = document.getElementById("trackTitle");
const trackArtist = document.getElementById("trackArtist");

const audioFormat = document.getElementById("audioFormat");
const audioBitrate = document.getElementById("audioBitrate");

const downloadButton = document.getElementById("downloadButton");


// =========================================================
// CURRENT TRACK
// =========================================================

let currentSpotifyUrl = "";


// =========================================================
// INITIAL STATE
// =========================================================

downloadButton.disabled = true;
downloadButton.textContent = "Download";


// =========================================================
// PASTE BUTTON
// =========================================================

pasteButton.addEventListener("click", async () => {

    try {

        const text =
            await navigator.clipboard.readText();

        if (!text) {

            inputNote.textContent =
                "Your clipboard is empty.";

            return;
        }

        spotifyUrl.value =
            text.trim();

        inputNote.textContent = "";

        spotifyUrl.focus();

    } catch (error) {

        inputNote.textContent =
            "Clipboard access was blocked. Paste the link manually.";
    }
});


// =========================================================
// ANALYZE BUTTON
// =========================================================

analyzeButton.addEventListener(
    "click",
    analyzeMusic
);


// =========================================================
// ENTER KEY
// =========================================================

spotifyUrl.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {

            analyzeMusic();
        }
    }
);


// =========================================================
// ANALYZE
// =========================================================

async function analyzeMusic() {

    const url =
        spotifyUrl.value.trim();

    inputNote.textContent = "";


    // -----------------------------------------------------
    // VALIDATION
    // -----------------------------------------------------

    if (!url) {

        inputNote.textContent =
            "Paste a Spotify link first.";

        spotifyUrl.focus();

        return;
    }


    if (!url.toLowerCase().includes("spotify.com")) {

        inputNote.textContent =
            "Please enter a valid Spotify URL.";

        spotifyUrl.focus();

        return;
    }


    // -----------------------------------------------------
    // SAVE URL
    // -----------------------------------------------------

    currentSpotifyUrl = url;


    // -----------------------------------------------------
    // BUTTON STATE
    // -----------------------------------------------------

    analyzeButton.disabled = true;

    analyzeButton.textContent =
        "Analyzing...";

    downloadButton.disabled = true;

    downloadButton.textContent =
        "Download";


    // -----------------------------------------------------
    // REQUEST
    // -----------------------------------------------------

    try {

        const response =
            await fetch(
                `${API_BASE}/api/music/analyze`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        url: url
                    })
                }
            );


        const data =
            await response.json();


        // -------------------------------------------------
        // ERROR
        // -------------------------------------------------

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to analyze the Spotify link."
            );
        }


        // -------------------------------------------------
        // DISPLAY TRACK
        // -------------------------------------------------

        displayTrack(data);


    } catch (error) {

        inputNote.textContent =
            error.message ||
            "Something went wrong.";

        downloadButton.disabled =
            true;

        downloadButton.textContent =
            "Download";


    } finally {

        analyzeButton.disabled =
            false;

        analyzeButton.textContent =
            "Analyze";
    }
}


// =========================================================
// DISPLAY TRACK
// =========================================================

function displayTrack(data) {

    currentSpotifyUrl =
        data.spotify_url ||
        currentSpotifyUrl;


    trackTitle.textContent =
        data.title ||
        "Unknown track";


    trackArtist.textContent =
        data.artist ||
        "Spotify track";


    // -----------------------------------------------------
    // THUMBNAIL
    // -----------------------------------------------------

    if (data.thumbnail) {

        trackThumbnail.src =
            data.thumbnail;

    } else {

        trackThumbnail.removeAttribute(
            "src"
        );
    }


    // -----------------------------------------------------
    // SHOW RESULTS
    // -----------------------------------------------------

    results.style.display =
        "block";


    // -----------------------------------------------------
    // ENABLE DOWNLOAD IMMEDIATELY
    // -----------------------------------------------------

    downloadButton.disabled =
        false;

    downloadButton.textContent =
        "Download";


    inputNote.textContent = "";


    // -----------------------------------------------------
    // SCROLL
    // -----------------------------------------------------

    results.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =========================================================
// CLOSE RESULTS
// =========================================================

closeResults.addEventListener(
    "click",
    () => {

        results.style.display =
            "none";

        downloadButton.disabled =
            true;

        downloadButton.textContent =
            "Download";
    }
);


// =========================================================
// DOWNLOAD BUTTON
// =========================================================

downloadButton.addEventListener(
    "click",
    downloadMusic
);


// =========================================================
// DOWNLOAD
// =========================================================

async function downloadMusic() {

    // -----------------------------------------------------
    // VALIDATION
    // -----------------------------------------------------

    if (!currentSpotifyUrl) {

        inputNote.textContent =
            "Please analyze a Spotify link first.";

        return;
    }


    // -----------------------------------------------------
    // PROTECT BUTTON
    // -----------------------------------------------------

    if (downloadButton.disabled) {

        return;
    }


    downloadButton.disabled =
        true;

    downloadButton.textContent =
        "Downloading...";

    inputNote.textContent = "";


    // -----------------------------------------------------
    // REQUEST DOWNLOAD
    // -----------------------------------------------------

    try {

        const response =
            await fetch(
                `${API_BASE}/api/music/download`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({

                        url: currentSpotifyUrl,

                        format:
                            audioFormat.value,

                        bitrate:
                            audioBitrate.value
                    })
                }
            );


        // -------------------------------------------------
        // CHECK RESPONSE
        // -------------------------------------------------

        if (!response.ok) {

            let errorMessage =
                "Unable to download the track.";

            try {

                const errorData =
                    await response.json();

                errorMessage =
                    errorData.detail ||
                    errorMessage;

            } catch (error) {

                // Response was not JSON.
            }

            throw new Error(
                errorMessage
            );
        }


        // -------------------------------------------------
        // RECEIVE AUDIO FILE
        // -------------------------------------------------

        const blob =
            await response.blob();


        if (!blob || blob.size === 0) {

            throw new Error(
                "The downloaded file was empty."
            );
        }


        // -------------------------------------------------
        // CREATE TEMPORARY DOWNLOAD URL
        // -------------------------------------------------

        const downloadUrl =
            window.URL.createObjectURL(
                blob
            );


        // -------------------------------------------------
        // CREATE DOWNLOAD LINK
        // -----------------------------------------------------

        const link =
            document.createElement("a");

        link.href =
            downloadUrl;


        // -------------------------------------------------
        // FILE NAME
        // -----------------------------------------------------

        const extension =
            audioFormat.value;

        const title =
            trackTitle.textContent
                .trim()
                .replace(
                    /[<>:"/\\|?*]/g,
                    ""
                );


        link.download =
            `${title || "download"}.${extension}`;


        // -------------------------------------------------
        // TRIGGER DOWNLOAD
        // -----------------------------------------------------

        document.body.appendChild(
            link
        );

        link.click();

        link.remove();


        // -------------------------------------------------
        // CLEANUP
        // -----------------------------------------------------

        window.URL.revokeObjectURL(
            downloadUrl
        );


    } catch (error) {

        console.error(
            "Download error:",
            error
        );


        inputNote.textContent =
            error.message ||
            "Something went wrong while downloading.";


    } finally {

        // -------------------------------------------------
        // RESTORE BUTTON
        // -------------------------------------------------

        downloadButton.disabled =
            false;

        downloadButton.textContent =
            "Download";
    }
}