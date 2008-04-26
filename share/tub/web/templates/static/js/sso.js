if(typeof(sso) == 'undefined') {
    sso = {};
}

sso.enhanceForm = function(selectId) {
    MochiKit.Signal.connect(selectId, 'onchange', function() {
        var value = MochiKit.DOM.$(selectId).value;
        document.location = value;
        });
}
