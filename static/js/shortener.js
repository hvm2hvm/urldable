// First, checks if it isn't implemented yet.
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}
//example usage: "{0} is dead, but {1} is alive! {0} {2}".format("ASP", "ASP.NET")

function SelectText(element) {
    var doc = document
        , text = doc.getElementById(element)
        , range, selection
    ;    
    if (doc.body.createTextRange) {
        range = document.body.createTextRange();
        range.moveToElementText(text);
        range.select();
    } else if (window.getSelection) {
        selection = window.getSelection();        
        range = document.createRange();
        range.selectNodeContents(text);
        selection.removeAllRanges();
        selection.addRange(range);
    }
}

function do_shorten() {
    var url = $("#urlbox").val();
    
    $.ajax("/shorten", {
        type: "POST",
        data: {
            url: url
        },
        dataType: "html",
        success: function(data) {
            $("#results").html(data);
            $("#title").html("Press CTRL+C");
        },
        error: function() {
            $("#results").html("<span>There was an error with the request</span>");
        }
    });
}

$(document).ready(function() {
    $("body").keydown(function(e){
        // $("#urlbox").focus();
        // $("#urlbox").val("");
        console.log("down: " + e.which + " " + e.ctrlKey);
        if (e.which == 86 && e.ctrlKey) { // CTRL+V
            $("#urlbox").focus();
            $("#urlbox").val("");
        }
    });
    $("body").keypress(function(e) {
        console.log("press: " + e.which + " " + e.ctrlKey);
    });
    $("body").keyup(function(e){
        console.log("up: " + e.which + " " + e.ctrlKey);
        if (e.which == 86 && e.ctrlKey) { // CTRL+V
            do_shorten();
        } else if (e.which == 67 && e.ctrlKey) {
            $("#title").html("You can now use the short URL <br />CTRL+V again for a new link");
        }
    });
    
});
