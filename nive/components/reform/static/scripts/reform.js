
/* 
 * Register a top-level callback to the reform.load() function 
 * this will be called when the DOM has finished loading. No need
 * to include the call at the end of the page.
 */
$(document).ready(function(){
    reform.load();
});



var reform_loaded = false;
var reform  = {
    callbacks: [],

    addCallback: function (oid, callback) {
        reform.callbacks.push([oid, callback])
    },

    clearCallbacks: function () {
        reform.callbacks = [];
    },

    load: function() {
      $(function() {
        if (!reform_loaded) {
            reform.processCallbacks();
            reform.focusFirstInput();
            reform.initControlset();
            reform_loaded = true;
      }});
    },
            

    processCallbacks: function () {
        $(reform.callbacks).each(function(num, item) {
            var oid = item[0];
            var callback = item[1];
            callback(oid);
        });
        reform.clearCallbacks();
    },

    maybeScrollIntoView: function(element_id) {
        var viewportWidth = $(window).width(),
            viewportHeight = $(window).height(),
            documentScrollTop = $(document).scrollTop(),
            documentScrollLeft = $(document).scrollLeft(),
            minTop = documentScrollTop,
            maxTop = documentScrollTop + viewportHeight,
            minLeft = documentScrollLeft,
            maxLeft = documentScrollLeft + viewportWidth,
            element = document.getElementById(element_id),
            elementOffset = $(element_id).offset();
        if (
            !(elementOffset.top > minTop && elementOffset.top < maxTop) &&
            !(elementOffset.left > minLeft && elementOffset.left < maxLeft)
            ) {
                element.scrollIntoView();
            };
    },

    focusFirstInput: function () {
        var input = $(':input').filter('[id ^= reformField]').first();
        if (input) {
            var raw = input.get(0);
            if (raw) {
                if (raw.type === 'text' || raw.type === 'file' || 
                    raw.type == 'password' || raw.type == 'text' || 
                    raw.type == 'textarea') { 
                    if (raw.className != "hasDatepicker") {
                        input.focus();
                    };
                };
            };
        };
    },

    initControlset: function () {
    	$(".input-controlset").each(function(num, select) {
    	    // set initial fields visible/invisible
    	    var values = $(select).data('controlset');
            for(i=0;i<=values.length;i++) {
                $('#item-'+values[i]).hide();
            }
        });
    	$(".input-controlset :selected").each(function(num, option) {
    	    // set initial fields visible/invisible
    	    var values = $(option).data('controlset');
            for(i=0;i<=values.length;i++) {
                $('#item-'+values[i]).show();
            }
        });
        $(".input-controlset").change(function() { 
    	    // trigger change and set fields visible/invisible
    	    var values = $(this).data('controlset');
            for(i=0;i<=values.length;i++) {
                $('#item-'+values[i]).hide();
            }
    	    var values = $('#'+this.id+' :selected').data('controlset');
            for(i=0;i<=values.length;i++) {
                $('#item-'+values[i]).show('slow');
            }
        });
    },
    
    randomString: function (length) {
        var chr='0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz';
        var chr = chr.split('');
    
        if (! length) {
            length = Math.floor(Math.random() * chr.length);
        };
    
        var str = '';
        for (var i = 0; i < length; i++) {
            str += chr[Math.floor(Math.random() * chr.length)];
        };
        return str;
    }

};
