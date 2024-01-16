const record = document.querySelector("#record");
    const stop1 = document.querySelector("#btn-stop");
    const soundClips = document.querySelector("#sound-clips");

    stop1.disabled = true;

    if (navigator.mediaDevices.getUserMedia) {
      console.log("getUserMedia supported.");

      let chunks = [];
      let mediaRecorder;
      let recordingInterval;
      let secondsElapsed = 0;

      const onSuccess = (stream) => {
        mediaRecorder = new MediaRecorder(stream);

        record.onclick = function () {
          if (mediaRecorder.state === "inactive") {
            startRecording();
            mediaRecorder.start();
            stop1.disabled = false;
            record.disabled = true;
          }
        };

        stop1.onclick = function () {
          mediaRecorder.stop();
          stop1.disabled = true;
          record.disabled = false;
          record.innerText = "Record";
          stopRecording();
        };

          mediaRecorder.onstop = function (e) {
              let clipContainer = document.createElement("article");
              let audio = document.createElement("audio");
              let deleteButton = document.createElement("button");
              let saveButton = document.createElement("button");

              clipContainer.classList.add("clip");
              audio.setAttribute("controls", "");
              deleteButton.textContent = "Delete";
              deleteButton.className = "delete";
              saveButton.textContent = "Save File";
              saveButton.className = "save";

              clipContainer.appendChild(audio);
              clipContainer.appendChild(deleteButton);
              clipContainer.appendChild(saveButton);
              soundClips.appendChild(clipContainer);

              audio.controls = true;
              let blob = new Blob(chunks, { type: "audio/ogg; codecs=opus" });
              chunks = [];
              let audioURL = window.URL.createObjectURL(blob);
              audio.src = audioURL;
              console.log("recorder stopped");

              deleteButton.onclick = (e) => {
                  evtTgt = e.target;
                  evtTgt.parentNode.parentNode.removeChild(evtTgt.parentNode);
              };

              saveButton.onclick = (e) => {
                console.log(blob);
                alert(`Save sends this audio to server`);
                fetch('/upload_audio', {
                method: 'POST',
                body: blob,
                headers: {
                    'Content-Type': 'audio/ogg; codecs=opus'
                  }
                })
                .then(response => response.text())
                .then(data => {
                    alert(data);
                })
                .catch(error => {
                    console.error('Erro ao enviar áudio para o servidor:', error);
                });
              };
          };

          mediaRecorder.ondataavailable = function (e) {
              chunks.push(e.data);
          };
      }; // onSuccess

      const onError = (err) => {
          console.log("The following error occured: " + err);
      };

      const startRecording = () => {
        record.disabled = true;
        stop1.disabled = false;
        record.innerText = "0:00";

        secondsElapsed = 0; 
        mediaRecorder.start();
        recordingInterval = setInterval(() => {
          const minutes = Math.floor(secondsElapsed / 60);
          const seconds = secondsElapsed % 60;

          record.innerText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
          secondsElapsed++;
        }, 1000);
      };

        const stopRecording = () => {
            record.disabled = false;
            stop1.disabled = true;
            mediaRecorder.stop();
            clearInterval(recordingInterval);
            record.innerText = "Record";
            secondsElapsed = 0
        };

        const updateTimer = () => {
            secondsElapsed++;

            const minutes = Math.floor(secondsElapsed / 60);
            const seconds = secondsElapsed % 60;

            record.innerText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

            if (secondsElapsed >= 30) {
                stopRecording();
            }
        };

      navigator.mediaDevices.getUserMedia({ audio: true }).then(onSuccess, onError);
  } else {
      console.log("getUserMedia not supported on your browser!");
  }