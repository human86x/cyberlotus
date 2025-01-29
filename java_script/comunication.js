
        // Placeholder for adding actions

        function logMessage(message) {
            const output = document.getElementById('consoleOutput');
            output.value += `\n${message}`;
            output.scrollTop = output.scrollHeight;
        }



        function calibrate() {
    const sequence = document.getElementById('sequence').value;
    logMessage(`Starting calibration for: ${sequence}`);

    if (sequence === "LOW") {
        fetch('/calibrate_ph_low')
        .then(response => response.json())
        .then(data => {
            console.log('pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching pH readings for LOW:', error);
        });
    } else if (sequence === "HIGH") {
        fetch('/calibrate_ph_high')
        .then(response => response.json())
        .then(data => {
            console.log('pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching pH readings for HIGH:', error);
        });
    } else {
        console.error('Invalid calibration sequence selected.');
    }

    // Send calibration command (implement backend communication here)
}


function simple_cal_low_Ph() {
    fetch('/simple_calibrate_ph_low')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}
function simple_cal_high_Ph() {
    fetch('/simple_calibrate_ph_high')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}

function solutionPh() {
    fetch('/ph_solution_test')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}


function baselinePh() {
    fetch('/ph_baseline_test')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}


        
function rawPh() {
    fetch('/get_raw_ph')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}


        
        function testPh() {
    fetch('/get_ph')
        .then(response => response.json())
        .then(data => {
            console.log('pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching pH readings:', error);
        });
}

        function fetchValue() {
            logMessage('Fetching current pH value...');
            // Fetch current pH value (implement backend communication here)
        }

        function saveConfig() {
            logMessage('Saving pH configuration...');
            // Save configuration to file or backend (implement here)
        }

        function loadConfig() {
            logMessage('Loading pH configuration...');
            // Load configuration from file or backend (implement here)
        }
