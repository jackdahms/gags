var job_id = data.job_id;
var debug = false; 

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
            job = JSON.parse(data);
            if (debug) {console.log(job);}
            if (job.lines.length > 0) {
                display_song(job.lines);
            } else {
                update_progress_bar(job.current, job.total);
                status();
            }
        },
        url: JOB_URL
    })}, 1000);
};

let update_progress_bar = function (current, total) {
    $("#spinningDiv").addClass("d-none");
    $("#progressDiv").removeClass("d-none");
    let bar = $("#progressBar");
    bar.text(current + "/" + total);
    let width = 10;
    if (total != 0) {
        width = Math.max(10, (current / total) * 100);
    }
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