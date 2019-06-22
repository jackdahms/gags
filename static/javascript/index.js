$("#generateForm").submit(function(event) {
    // .submit() doesn't run before submitting on firefox
    // https://stackoverflow.com/questions/21938788/jquery-function-before-form-submission
    event.preventDefault();
    $("#loadingDiv").removeClass("d-none");
    $(this).unbind('submit').submit(); 
});