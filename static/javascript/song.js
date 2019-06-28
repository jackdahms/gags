let status = function() {
    setTimeout(function() {$.ajax({
        data: {
            'job_id': job_id
        },
        error: function(xhr, text_status, error_thrown) {
            console.log(xhr.responseText + ',' + text_status + ',' + error_thrown);
            if (text_status == "timeout") {
                status();
            }
        },
        success: function(data, text_status, xhr) {
            data = JSON.parse(data);
            let total = data.song_count;
            let current = data.current_song;
            if (total == -1) {
                // We're still counting songs
                status();
            } else if (current == total) {
                // Display lyrics
                display_song(data.lyrics);
            } else {
                // Display progress bar
                update_progress_bar(current, total);
                status();
            }
        },
        url: job_url
    })}, 1000);
};

let update_progress_bar = function (current, total) {
    $("#spinningDiv").addClass("d-none");
    $("#progressDiv").removeClass("d-none");
    bar = $("#progressBar");
    bar.text(current + "/" + total);
    width = Math.max(10, (current / total) * 100);
    bar.css("width", width + "%");
}

let display_song = function(lyrics) {
    $("#spinningDiv").addClass("d-none");
    $("#progressDiv").addClass("d-none");
    song = $("#songDiv");
    song.removeClass("d-none");

    for (let i = 0; i < lyrics.length; i++) {
        p = $("<p></p>");
        p.addClass("text-center rounded w-100 py-1 my-0");
        p.html("&nbsp;" + lyrics[i]);
        if (i % 2 == 0) {
            p.css("background", "#f2f2f2");
        }
        song.append(p)
    }
}

status();