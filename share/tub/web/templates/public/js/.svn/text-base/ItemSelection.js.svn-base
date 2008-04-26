if(typeof(Cms) == 'undefined') {
    Cms = {};
}

if(typeof(Cms.Forms) == 'undefined') {
    Cms.Forms = {};
}

if(typeof(Cms.Forms.ItemSelection) == 'undefined') {
    Cms.Forms.ItemSelection = {};
}

Cms.Forms.ItemSelection.popup = function(elementId, types) {
    var value = document.getElementById(elementId).value;
    var url = '/content/_itemselector_?element_id='+escape(elementId)
    url = url + '&value='+escape(value);
    if(types!='') {
      url = url +'&types='+escape(types);
    }
    var popup = window.open(url, 'ItemSelection', 'height=500,width=600,resizable,scrollbars');

    popup.callback = function(formValues) {
        // Set the description
        descriptionId = '#'+elementId+"-description"
        $(descriptionId).empty()
        if( formValues.type != '') {
            var parts = formValues.type.split('.');
            var type = parts[parts.length-1];
            $(descriptionId).append('<strong>Type:</strong><span>'+type+'</span><br />');
        }
        if(formValues.categories != '') {
            $(descriptionId).append('<strong>Categories:</strong><span>'+formValues.categories.join(',')+'</span>');
        }
        
        // Set the owning field to an encoded version of the form
        document.getElementById(elementId).value = formValues.toString();
    }
    popup.focus();
    return false;
}

Cms.Forms.ItemSelection.popupForReST = function(elementId,types,format) {
    var url = '/content/_itemselector_?element_id='+escape(elementId)
    if(types!='') {
      url = url +'&types='+escape(types);
    }
    
    var popup = window.open(url, 'ItemSelection', 'height=500,width=600,resizable,scrollbars');
    popup.callback = function(formValues) {
      alert(format);
      if (format == 'markdown') {
        var tag = '\n\ncmsitemselection://' + formValues.toString() + "\n\n";
      }
      if (format == 'rest') {
        var tag = '\n\n.. cmsitemselection:: ' + formValues.toString() + "\n\n\n";
      }
      Cms.Forms.ItemSelection.insertTextAtCursor(elementId, tag);
    }
    popup.focus();
    return false;
}

Cms.Forms.ItemSelection.insertTextAtCursor = function(owningFieldId, text) {
    // Based on www.alexking.org
    var owningDoc = document;
    var owningField = document.getElementById(owningFieldId);

    // IE support
    if (owningDoc.selection) {
        owningField.focus();
        sel = owningDoc.selection.createRange();
        sel.text = text;
    }
    //MOZILLA/NETSCAPE support
    else if (owningField.selectionStart || owningField.selectionStart == '0') {
        var startPos = owningField.selectionStart;
        var endPos = owningField.selectionEnd;
        owningField.value = owningField.value.substring(0, startPos)
        + text
        + owningField.value.substring(endPos, owningField.value.length);
    } else {
        owningField.value += text;
    }

}
