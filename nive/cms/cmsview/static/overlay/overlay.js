    (function ($) {  
      
        var _settings = {  
            overlayOpacity: .85, // Use this value if not set in CSS or HTML  
            id: 'modal',  
            src: function (sender) {  
                return jQuery(sender).attr('href');  
            },  
            fadeInSpeed: 0,  
            fadeOutSpeed: 0  
        }  
      
        /********************************** 
        * DO NOT CUSTOMIZE BELOW THIS LINE 
        **********************************/  
        $.niveOverlay = function (id) {  
            if(id) $(id+" a[rel^='niveOverlay']").attr("onClick", "$(this).modal().open(); return false;");
            else   $("a[rel^='niveOverlay']").attr("onClick", "$(this).modal().open(); return false;");
        }  
        $.modal = function (options) {  
            return _modal(this, options);  
        }  
        $.modal.open = function () {  
            _modal.open();  
        }  
        $.modal.close = function () {  
            _modal.close();  
        }  
        $.fn.modal = function (options) {  
            return _modal(this, options);  
        }  
        _modal = function (sender, params) {  
            this.options = {  
                parent: null,  
                overlayOpacity: null,  
                id: null,  
                content: null,  
                modalClassName: null,  
                imageClassName: null,  
                closeClassName: null,  
                overlayClassName: null,  
                src: null  
            }  
            this.options = $.extend({}, options, _defaults);  
            this.options = $.extend({}, options, _settings);  
            this.options = $.extend({}, options, params);  
            this.close = function (url) {
                jQuery('.' + options.modalClassName + ', .' + options.overlayClassName).fadeOut(_settings.fadeOutSpeed, function () { jQuery(this).unbind().remove(); if(!url) location.reload(); else {location.href=url;} });  
            }  
            this.cancel = function () {
                jQuery('.' + options.modalClassName + ', .' + options.overlayClassName).fadeOut(_settings.fadeOutSpeed, function () { jQuery(this).unbind().remove(); });  
            }  
            this.open = function () {  
                if (typeof options.src == 'function') {  
                    options.src = options.src(sender)  
                } else {  
                    options.src = options.src || _defaults.src(sender);  
                }  
      
                var fileExt = /^.+\.((jpg)|(gif)|(jpeg)|(png)|(jpg))$/i;  
                var contentHTML = '';  
                if (fileExt.test(options.src)) {  
                    contentHTML = '<div class="' + options.imageClassName + '"><img src="' + options.src + '"/></div>';  
      
                } else {  
                    contentHTML = '<iframe frameborder="0" allowtransparency="true" src="' + options.src + '"></iframe>';  
                }  
                options.content = options.content || contentHTML;  
      
                if (jQuery('.' + options.modalClassName).length && jQuery('.' + options.overlayClassName).length) {  
                    jQuery('.' + options.modalClassName).html(options.content);  
                } else {  
                    $overlay = jQuery((_isIE6()) ? '<iframe src="BLOCKED SCRIPT\'<html></html>\';" scrolling="no" frameborder="0" class="' + options.overlayClassName + '"></iframe><div class="' + options.overlayClassName + '"></div>' : '<div class="' + options.overlayClassName + '"></div>');  
                    $overlay.hide().appendTo(options.parent);  
      
                    $modal = jQuery('<div id="' + options.id + '" class="' + options.modalClassName + '" >' + options.content + '</div>');  
                    $modal.hide().appendTo(options.parent);  
      
                    $close = jQuery('<a id="' + options.closeClassName + '"></a>');  
                    $close.appendTo($modal);  
      
                    var overlayOpacity = _getOpacity($overlay.not('iframe')) || options.overlayOpacity;  
                    $overlay.fadeTo(0, 0).show().not('iframe').fadeTo(_settings.fadeInSpeed, overlayOpacity);  
                    $modal.fadeIn(_settings.fadeInSpeed);  
      
                    $close.click(function () { jQuery.modal().close(); });  
                    /*$overlay.click(function () { if(this.blocked && !confirm("Close form?")) return; jQuery.modal().cancel(); }); */ 
                }  
            }  
            return this;  
        }  
        _isIE6 = function () {  
            if (document.all && document.getElementById) {  
                if (document.compatMode && !window.XMLHttpRequest) {  
                    return true;  
                }  
            }  
            return false;  
        }  
        _getOpacity = function (sender) {  
            $sender = jQuery(sender);  
            opacity = $sender.css('opacity');  
            filter = $sender.css('filter');  
      
            if (filter.indexOf("opacity=") >= 0) {  
                return parseFloat(filter.match(/opacity=([^)]*)/)[1]) / 100;  
            }  
            else if (opacity != '') {  
                return opacity;  
            }  
            return '';  
        }  
        _defaults = {  
            parent: '#container',
            overlayOpacity: 70,
            id: 'modal',  
            content: null,  
            blocked: false,
            modalClassName: 'modal-window',  
            imageClassName: 'modal-image',  
            closeClassName: 'close-window',  
            overlayClassName: 'modal-overlay',  
            src: function (sender) {  
                return jQuery(sender).attr('href');  
            }  
        }  
    })(jQuery);  