$(function(){


    if (document.getElementById('dealtimer')) {
        DealTimer();
    }

    function DealTimer(){

        // Get the current date and time in milliseconds since the epoch
        const now = Date.now();

        // Calculate the target date 4 days in the future in milliseconds since the epoch
        const targetDate = now + (4 * 24 * 60 * 60 * 1000);

        // Convert the target date to seconds since the epoch
        const targetDateInSeconds = Math.floor(targetDate / 1000);

        // Set the target date in seconds since the epoch
        //  const targetDateInSeconds = 1735689599; // Example: December 31, 2024, 23:59:5
        // Update the countdown every second
        const countdown = setInterval(function() {
            // Get the current date and time in seconds since the epoch
            const nowInSeconds = Math.floor(Date.now() / 1000);
            
            // Calculate the difference between the target date and the current date
            const difference = targetDateInSeconds - nowInSeconds;
            
            // Calculate time units
            const days = Math.floor(difference / (60 * 60 * 24));
            const hours = Math.floor((difference % (60 * 60 * 24)) / (60 * 60));
            const minutes = Math.floor((difference % (60 * 60)) / 60);
            const seconds = difference % 60;
            
            // Display the countdown in the format "DD:HH:MM:SS"
            document.getElementById('dealtimer').innerHTML = `${days.toString().padStart(2, '0')}:${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // If the countdown is over, clear the interval
            if (difference <= 0) {
            clearInterval(countdown);
            document.getElementById('dealtimer').innerHTML = "Countdown expired!";
            }
        }, 1000);
    }

  

});