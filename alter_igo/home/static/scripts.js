var i=1;
var nt=0;
var np=0;


$('#submit').click(function(){
    $.getJSON("/home/process", {
        command: $('#cmd').val(),
    }, function(data){
        var wrapper_id = "wrapper" + data.outputs[4];
        $('.content').append('<div id="' + wrapper_id + '" class="wrapper"></div>');
        $('#' + wrapper_id).append('<div class="commandwrapper"><div class="numlabel">['+i+']: </div><div class="command_disp"><b>'+data.outputs[1]+'</b></div><div class="feedback-btns"><button class="thumbsup" id="thumbsup'+data.outputs[4]+'" type="button" onclick="positive('+data.outputs[4]+')" title="This worked well"><i class="bx bx-like"></i></button><button class="thumbsdown" id="thumbsdown'+data.outputs[4]+'" type="button" onclick="negative('+data.outputs[4]+')" title="This did not work well"><i class="bx bx-dislike"></i></button><button class="edit" id="edit'+i+'" type="button" onclick="editcode('+i+')"><i class="bx bx-edit"></i></button><button class="delete" id="delete'+data.outputs[4]+'" type="button" onclick="deleteentry('+data.outputs[4]+')"><i class="bx bx-trash"></i></button></div></div></div>');
        if (document.getElementById('checkbox').checked) {
            $('#' + wrapper_id).append("<div class='codewrapper'><button data-toggle='collapse' class='cobutton' data-target='#code"+i+"'></button><div class='collapse in' id='code"+i+"'><pre><code class='language-python'>"+data.outputs[2]+"</code></pre></div></div>");
        } else if (data.outputs[3] == "") {
            $('#' + wrapper_id).append("<div class='codewrapper'><button data-toggle='collapse' class='cobutton' data-target='#code"+i+"'></button><div class='collapse in' id='code"+i+"'><pre><code class='language-python'>"+data.outputs[2]+"</code></pre></div></div>");
        } else {
            $('#' + wrapper_id).append("<div class='codewrapper'><button data-toggle='collapse' class='cobutton collapsed' data-target='#code"+i+"'></button><div class='collapse' id='code"+i+"'><pre><code class='language-python'>"+data.outputs[2]+"</code></pre></div></div>");
        }
        let outputdiv = document.createElement('div');
        outputdiv.classList = "output";
        if (data.outputs[0] == 'image') {
            $(outputdiv).append(data.outputs[3]);
            $('#' + wrapper_id).append(outputdiv);
            var imgsrc = document.getElementById('image'+np).src;
            $(outputdiv).append("<div class='dl_btn'><a href="+imgsrc+" download='image"+np+"'>Download as PNG</a></div>");
            np++;
        } else if (data.outputs[0] == 'dataframe') {
            $(outputdiv).append(data.outputs[3]);
            $('#' + wrapper_id).append(outputdiv);
            $(outputdiv).append("<div class='dl_btn'><a href='#' onclick='download_table_as_csv("+'table'+nt+");'>Download as CSV</a></div>");
            nt++;
        } else if (data.outputs[3] !== "") {
            $(outputdiv).append('<pre><code class="language-plaintext">'+data.outputs[3]+'</code></pre>');
            $('#' + wrapper_id).append(outputdiv);
        } else {
            $(outputdiv).append('<p>No output (I\'m hidden by default)</p>');
            $('#' + wrapper_id).append(outputdiv);
            $(outputdiv).hide();
        }
        if (data.outputs[2] == '') {
            alert("Sorry, I couldn't understand your request.");
        }
        $('.content').append('<hr>');
        hljs.highlightAll();
        document.getElementById("cmd").value = "";
        $('html,body').animate({scrollTop: document.body.scrollHeight},"fast");
    i++;
});
});

$('#clear').click(function(){
    i=1;
    nt=0;
    np=0;
    $.getJSON('/clear', {
        value: 1,
    }, function(data){
        $('.content').empty();
        hljs.highlightAll();
        document.getElementById("cmd").value = "";
    });
});

$('#showcode').change(function () {
    if ($(this).is(":checked")) {
        $('#table').show();
    } else {
        $('#table').hide();
    }
});

$('#cmd').keydown(function(e){
    if(e.ctrlKey && (e.keyCode == 13 || e.keyCode == 10)) {
        e.preventDefault();
        $('#submit').click();
        document.getElementById("cmd").value = "";
    }
});

var sideBar = document.getElementById('entry');
var arrBtn = document.getElementById('open-close-btn');
var arrIco = document.getElementById('arrowIcon');
var hideOnShrink = document.getElementById('entry-main-content');
var entryTitle = document.getElementById('entry-title');
var mainDiv = document.getElementById('display');
$('#open-close-btn').click(function() {
    if (arrIco.classList == "bx bx-arrow-from-right") {
        arrIco.classList = "bx bx-arrow-from-left";
        sideBar.style.width = "6rem";
        hideOnShrink.style.opacity = "0";
        entryTitle.style.opacity = "0";
        mainDiv.style.marginLeft = "6rem";
    } else {
        arrIco.classList = "bx bx-arrow-from-right";
        sideBar.style.width = "33vw";
        hideOnShrink.style.opacity = "1";
        entryTitle.style.opacity = "1";
        mainDiv.style.marginLeft = "33vw";
    };
});


$body = $("body");
$(document).on({
    ajaxStart: function() { $body.addClass("loading");    },
    ajaxStop: function() { $body.removeClass("loading"); }    
});


function download_table_as_csv(table_id) {
    var rows = document.querySelectorAll('#'+table_id.id+' tr');
    var csv = [];
    for (var i = 0; i < rows.length; i++) {
        var row = [], cols = rows[i].querySelectorAll('td, th');
        for (var j = 0; j < cols.length; j++) {
            var data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ')
            data = data.replace(/"/g, '""');
            // Push escaped string
            row.push('"' + data + '"');
        }
        csv.push(row.join(','));
    }
    var csv_string = csv.join('\n');

    var filename = 'export_' + table_id.id + '.csv';
    var link = document.createElement('a');
    link.style.display = 'none';
    link.setAttribute('target', '_blank');
    link.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv_string));
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function positive(button_id) {
    $.getJSON('/positive_feedback', {
            db_id: button_id,
        }, function(data) {
            var elem_up = document.getElementById('thumbsup'+button_id)
            var elem_dn = document.getElementById('thumbsdown'+button_id)
            if (elem_up.style.color == 'green') {
                elem_up.style.color = 'gray';
            } else {
                elem_up.style.color = 'green';
                elem_dn.style.color = 'gray';
            }
        });
}

function negative(button_id) {
    $.getJSON('/negative_feedback', {
            db_id: button_id,
        }, function(data) {
            var elem_up = document.getElementById('thumbsup'+button_id)
            var elem_dn = document.getElementById('thumbsdown'+button_id)
            if (elem_dn.style.color == 'red') {
                elem_dn.style.color = 'gray';
            } else {
                elem_dn.style.color = 'red';
                elem_up.style.color = 'gray';
            }
        });
}

function editcode(code_div_id) {
    var targetdiv = document.getElementById('code'+code_div_id);
    var origcode = targetdiv.textContent;
    var editableText = document.createElement("textarea");
    var editButton = document.getElementById('edit'+code_div_id);
    var confirmButton = document.createElement("button");
    if (targetdiv.classList == "collapse") {
        targetdiv.classList = "collapse in";
        targetdiv.previousSibling.classList = "cobutton"
    }
    $(targetdiv).show();
    let h = $(targetdiv).css('height');
    $(targetdiv).hide();
    editableText.classList = "editbox";
    editableText.id = "editcode"+code_div_id;
    editableText.style.height = h;
    editableText.style.width = "100%";
    editableText.value = origcode;
    confirmButton.classList = "confirm";
    confirmButton.id = "confirm"+code_div_id;
    let icon = document.createElement("i");
    icon.classList = "bx bx-check";
    confirmButton.appendChild(icon);
    confirmButton.type = "button";
    confirmButton.setAttribute("onclick", "editconfirm("+code_div_id+")");
    editableText.value = origcode; 
    targetdiv.insertAdjacentElement("afterend", editableText);
    editButton.replaceWith(confirmButton);
    cancelButton = document.createElement("button");
    cancelButton.classList = "cancel";
    cancelButton.id = "cancel"+code_div_id;
    let icon2 = document.createElement("i");
    icon2.classList = "bx bx-x";
    cancelButton.appendChild(icon2);
    confirmButton.insertAdjacentElement("afterend", cancelButton);
    cancelButton.type = "button";
    cancelButton.setAttribute("onclick", "editcancel("+code_div_id+")");
    $(editableText).keydown(function(e) {
        if(e.keyCode == 9) {
            var start = this.selectionStart;
            var end = this.selectionEnd;
            var $this = $(this);
            var value = $this.val();
            $this.val(value.substring(0, start) + "\t" + value.substring(end));
            this.selectionStart = this.selectionEnd = start + 1;
            e.preventDefault();
        }
        if(e.ctrlKey && (e.keyCode == 13 || e.keyCode == 10)) {
            e.preventDefault();
            confirmButton.click();
            cancelButton.remove();
        }
        if(e.key === "Escape") {
            e.preventDefault();
            cancelButton.click();
        }
    });
}

function editconfirm(code_div_id) {
    var editbox = document.getElementById("editcode"+code_div_id);
    var confirmButton = document.getElementById('confirm'+code_div_id);
    var targetdiv = document.getElementById('code'+code_div_id);
    var newdiv = document.createElement("div");
    var editButton = document.createElement("button");
    var editedcode = editbox.value;
    var cancelButton = document.getElementById('cancel'+code_div_id);
    targetdiv.remove();
    newdiv.classList = "collapse in";
    newdiv.id = "code"+code_div_id;
    newdiv.appendChild(document.createElement("pre"));
    newdiv.lastChild.appendChild(document.createElement("code"));
    newdiv.lastChild.lastChild.class = "language-python";
    newdiv.lastChild.lastChild.textContent = editedcode;
    editButton.classList = "edit";
    editButton.id = "edit"+code_div_id;
    let icon = document.createElement("i");
    icon.classList = "bx bx-edit";
    editButton.append(icon);
    editButton.type = "button";
    editButton.setAttribute("onclick", "editcode("+code_div_id+")");
    confirmButton.replaceWith(editButton);
    cancelButton.remove();
    editbox.replaceWith(newdiv);
    var record_id = editButton.previousSibling.id.replace(/[^0-9]/g,'');
    var outputdiv = newdiv.parentElement.nextSibling;
    $.getJSON('/edit', {
        ref: record_id,
        new_code: editedcode,
    }, function(data) {
        // parse the outputtype and output passed back, change outputdiv accordingly
        var newoutput = document.createElement("div");
        newoutput.classList = "output";
        if (data.outputs[0] == 'image') {
            $(newoutput).append(data.outputs[1]);
            $(outputdiv).replaceWith(newoutput);
            var imgsrc = document.getElementById('image'+np).src;
            $(newoutput).append("<div class='dl_btn'><a href="+imgsrc+" download='image"+np+"'>Download as PNG</a></div>");
            np++;
        } else if (data.outputs[0] == 'dataframe') {
            $(newoutput).append(data.outputs[1]);
            $(outputdiv).replaceWith(newoutput);
            $(newoutput).append("<div class='dl_btn'><a href='#' onclick='download_table_as_csv("+'table'+nt+");'>Download as CSV</a></div>")
            nt++;
        } else if (data.outputs[1] !== "") {
            $(newoutput).append('<pre><code class="language-plaintext">'+data.outputs[1]+'</code></pre>');
            $(outputdiv).replaceWith(newoutput);
        } else {
            $(newoutput).append('<p>No output (I\'m hidden by default)</p>');
            $(newoutput).hide();
            $(outputdiv).replaceWith(newoutput);
        }
        hljs.highlightAll();
    })
}

function editcancel(code_div_id) {
    var targetdiv = document.getElementById('code'+code_div_id);
    var origcode = targetdiv.textContent;
    var editbox = document.getElementById("editcode"+code_div_id);
    var confirmButton = document.getElementById('confirm'+code_div_id);
    var cancelButton = document.getElementById('cancel'+code_div_id);
    var editButton = document.createElement("button");
    editButton.classList = "edit";
    editButton.id = "edit"+code_div_id;
    let icon = document.createElement("i");
    icon.classList = "bx bx-edit";
    editButton.append(icon);
    editButton.type = "button";
    editButton.setAttribute("onclick", "editcode("+code_div_id+")");
    confirmButton.replaceWith(editButton);
    cancelButton.remove();
    editbox.remove();
    $(targetdiv).show();
    hljs.highlightAll();
}

function deleteentry(record_id) {
    var wrapper = document.getElementById('wrapper'+record_id);
    var linebreak = wrapper.nextSibling;
    $.getJSON('/delete_record', {
        db_id: record_id,
    }, function(data) {
        wrapper.remove();
        linebreak.remove();
    })
}

$('textarea').keydown(function(e) {
    if(e.keyCode == 9) {
        var start = this.selectionStart;
        var end = this.selectionEnd;
        var $this = $(this);
        var value = $this.val();
        $this.val(value.substring(0, start) + "\t" + value.substring(end));
        this.selectionStart = this.selectionEnd = start + 1;
        e.preventDefault();
    }
});