function openPopup(audioID, audioFileName) {
    var popup = document.getElementById("popup");
    popup.style.display = "block";
    }
function closePopup() {
    var popup = document.getElementById("popup");
    popup.style.display = "none";
}   

function transformToText(audioID) {
    var url_transform_audio = "/transform_audio";

    var textResult = document.getElementById("textResult");
    textResult.innerHTML = "Processando...";

    fetch(url_transform_audio + "?audioID=" + audioID)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro na requisição: ${response.status} ${response.statusText}`);
            }
            return response.text();
        })
        .then(data => {
            textResult.innerHTML = data;
        })
        .catch(error => {
            textResult.innerHTML = "Erro na transformação. Verifique o console para detalhes.";
            console.error(error);
        });
}       

function confirmText(audioID) {
    var url_confirm_text = "/confirm_text";
    var textResult = document.getElementById("textResult").innerHTML;

    fetch(url_confirm_text, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ audioID: audioID, text: textResult })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro na requisição: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                var mensagemSucesso = document.getElementById("mensagemSucesso");
                mensagemSucessso.innerHTML = 'Texto confirmado com sucesso!';


                var table = document.getElementById("audioTable");
                var rows = table.getElementsByTagName("tr");

                for (var i = 0; i < rows.length; i++) {
                    var cells = rows[i].getElementsByTagName("td");

                    var audioIDCell = cells[1];

                    if (audioIDCell.innerHTML === audioID) {
                        cells[2].innerHTML = "Audio Processado";
                        cells[3].innerHTML = "UploadTime";
                        cells[4].innerHTML = '<button onclick="showDetails(' + audioID + ')">Detalhes</button>';
                        break;
                    }
                }
            } else {
                console.error('Erro ao confirmar o texto:', data.error);
            }
        })
}

function showDetails(audioID) {
    var url_detalhes_audio = "/detalhes_audio";

    fetch(url_detalhes_audio + "?audioID=" + audioID)
        .then(response => response.json())
        .then(data => {
            var detalhesPopup = document.getElementById("detalhesPopup");
            detalhesPopup.innerHTML = `
                <p>TextID: ${data.TextID}</p>
                <p>Text: ${data.Text}</p>
                <p>Conversion Data: ${data.ConversionData}</p>
            `;

            detalhesPopup.style.display = "block";
        })
        .catch(error => console.error('Erro na requisição:', error));
}