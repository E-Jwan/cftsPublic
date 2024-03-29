if (authStatus == "prompt") {
    codeSubmit = document.getElementById("codeSubmit")
    codeInput = document.getElementById("codeInput")

    function submitCode() {
        window.location = window.location + "/" + codeInput.value
    }

    codeSubmit.addEventListener('click', function() {
        submitCode()
    }, false);

    codeInput.addEventListener('keypress', function(e) {
        if (e.keyCode == 13) {
            submitCode()
        }
    }, false);

} else {
    history.pushState(null, "", location.href.split("/").slice(0, 5).join('/'))
    if (authStatus == "not authorized") {
        alert("Request Code entered is not correct")
        window.location = window.location
    } else if (authStatus == "authorized") {
        passphraseSubmit = document.getElementById("passphraseSubmit")
        passphraseInput = document.getElementById("passphraseInput")

        function submitPassphrase() {
            if (passphraseInput.value != "") {
                window.location = "/download-drop/" + dropID + "/" + passphraseInput.value
            } else {
                alert("Enter Decryption Phrase from email")
            }
        }

        passphraseSubmit.addEventListener('click', function() {
            submitPassphrase()
        }, true);


        passphraseInput.addEventListener('keypress', function(e) {
            if (e.keyCode == 13) {
                submitPassphrase()
                $("#passphraseModal").modal('hide')
            }
        }, false);
    }
}