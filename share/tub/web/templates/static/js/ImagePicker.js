if(typeof(Cms) == 'undefined') {
    Cms = {};
}

if(typeof(Cms.Forms) == 'undefined') {
    Cms.Forms = {};
}

if(typeof(Cms.Forms.ImagePicker) == 'undefined') {
    Cms.Forms.ImagePicker = {};
}

if(typeof(Cms.Forms.GalleryPicker) == 'undefined') {
    alert('undefined');
    Cms.Forms.GalleryPicker = {};
}

Cms.Forms.ImagePicker.popup = function(elementId,type) {
    var url = '/content/system/assets/assetbrowser';
    url = url + '?searchOwningId='+elementId+'&searchType='+type;
    var popup = window.open(url, 'ImagePicker', 'height=500,width=900,resizable,scrollbars');
    popup.focus();
    return false;
}

Cms.Forms.GalleryPicker.popup = function(elementId,type) {
    alert('ingp');
    var url = '/ecommerce/system/assets/assetbrowser';
    url = url + '?searchOwningId='+elementId+'&searchType='+type;
    var popup = window.open(url, 'GalleryPicker', 'height=500,width=900,resizable,scrollbars');
    popup.focus();
    return false;
}
